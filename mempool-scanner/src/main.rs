use ethers::prelude::*;
use std::env;
use std::fs;
use std::io::Write;
use std::sync::Arc;
use std::path::Path;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load env vars (optional, assuming they are set in shell)
    let rpc_url = env::var("RPC_URL").expect("RPC_URL must be set");
    
    println!("Connecting to WebSocket...");
    let provider = Provider::<Ws>::connect(&rpc_url).await?;
    let provider = Arc::new(provider);
    println!("Connected to {}", rpc_url);

    // Ensure temp directory exists
    let temp_dir = Path::new("temp");
    if !temp_dir.exists() {
        fs::create_dir(temp_dir)?;
    }

    // Subscribe to pending transactions
    let mut stream = provider.subscribe_pending_txs().await?;
    println!("Listening for pending transactions...");

    while let Some(tx_hash) = stream.next().await {
        let provider = provider.clone();
        tokio::spawn(async move {
            if let Err(e) = process_transaction(provider, tx_hash).await {
                // Ignore "not found" errors as txs might be dropped from mempool
                if !e.to_string().contains("not found") {
                    eprintln!("Error processing {:?}: {}", tx_hash, e);
                }
            }
        });
    }

    Ok(())
}

async fn process_transaction(provider: Arc<Provider<Ws>>, tx_hash: TxHash) -> Result<(), Box<dyn std::error::Error>> {
    let tx = provider.get_transaction(tx_hash).await?;

    if let Some(tx) = tx {
        // Detect Contract Creation: 'to' field is None
        if tx.to.is_none() {
            println!("[\u{26A1}] Contract Creation Detected: {:?}", tx_hash);

            // Save Bytecode (Input Data)
            let bytecode_path = format!("temp/{:?}_bytecode.bin", tx_hash);
            let mut file = fs::File::create(&bytecode_path)?;
            file.write_all(&tx.input)?;
            println!("Saved bytecode: {}", bytecode_path);

            // Attempt to fetch source code (Requires waiting for mining)
            // In a real bot race, we analyze bytecode directly. 
            // But per requirements, we try to get source via Etherscan.
            if let Ok(api_key) = env::var("ETHERSCAN_API_KEY") {
                tokio::spawn(async move {
                    if let Err(e) = fetch_and_save_source(provider, tx_hash, api_key).await {
                        eprintln!("Failed to fetch source for {:?}: {}", tx_hash, e);
                    }
                });
            }
        }
    }
    Ok(())
}

async fn fetch_and_save_source(provider: Arc<Provider<Ws>>, tx_hash: TxHash, api_key: String) -> Result<(), Box<dyn std::error::Error>> {
    // Wait for transaction to be mined to get the contract address
    // Timeout after 60 seconds
    let receipt = tokio::time::timeout(
        std::time::Duration::from_secs(60),
        provider.get_transaction_receipt(tx_hash)
    ).await??;

    if let Some(receipt) = receipt {
        if let Some(contract_address) = receipt.contract_address {
            println!("Contract deployed at: {:?}", contract_address);
            
            // Wait a bit for Etherscan to index (usually takes time)
            tokio::time::sleep(std::time::Duration::from_secs(10)).await;

            let url = format!(
                "https://api.etherscan.io/api?module=contract&action=getsourcecode&address={:?}&apikey={}",
                contract_address, api_key
            );

            let resp = reqwest::get(&url).await?.json::<serde_json::Value>().await?;
            
            if let Some(result) = resp.get("result") {
                if let Some(arr) = result.as_array() {
                    if let Some(first) = arr.first() {
                        if let Some(source) = first.get("SourceCode") {
                            let source_str = source.as_str().unwrap_or("");
                            if !source_str.is_empty() {
                                let source_path = format!("temp/{:?}_source.sol", tx_hash);
                                fs::write(&source_path, source_str)?;
                                println!("Saved source code: {}", source_path);
                            }
                        }
                    }
                }
            }
        }
    }
    Ok(())
}
