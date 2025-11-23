import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

import yaml
from langchain_community.chat_models import ChatOllama

class PoCGenerator:
    """
    Agent responsible for generating PoC exploits.
    """

    def __init__(self):
        with open("config/settings.yaml", "r") as f:
            config = yaml.safe_load(f)

        self.llm = ChatOllama(
            base_url=config["llm"]["base_url"],
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"]
        )

    def generate_exploit(self, source_code: str, vulnerability_info: str) -> str:
        """
        Generates a Solidity test contract to exploit the described vulnerability.
        """
        logger.info("Generating PoC exploit...")

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Exploit Developer.
Your task is to write a Foundry test (Solidity) that proves the existence of a vulnerability.

You will be given:
1. The Target Contract Source Code.
2. A description of the Vulnerability.

Output ONLY the Solidity code for the test contract.
- Import `forge-std/Test.sol`.
- Inherit from `Test`.
- Create a `setUp()` function to deploy the target.
- Create a `testExploit()` function that triggers the vulnerability.
- Use `assert` statements to prove the exploit worked (e.g., stolen funds, broken invariant).
- Ensure the code is a complete, compilable Solidity file (pragma, imports, contract).
- Use `pragma solidity ^0.8.0;` or compatible version.

Do not include markdown formatting or explanations. Just the code.
"""),
            ("user", """Target Contract:
```solidity
{source_code}
```

Vulnerability:
{vulnerability_info}

Generate Exploit Test:""")
        ])

        chain = prompt | self.llm | StrOutputParser()
        
        try:
            response = chain.invoke({
                "source_code": source_code,
                "vulnerability_info": vulnerability_info
            })
            # Clean up markdown if present
            response = response.replace("```solidity", "").replace("```", "").strip()
            return response
        except Exception as e:
            logger.error(f"PoC generation failed: {e}")
            return ""

    def generate_fuzz_test(self, source_code: str, property_desc: str) -> str:
        """
        Generates a Foundry fuzz/invariant test.
        """
        logger.info("Generating Fuzz test...")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Smart Contract Fuzzing Engineer.
Your task is to write a Foundry property-based test (Fuzz Test) to check an invariant.

Output ONLY the Solidity code.
- Import `forge-std/Test.sol`.
- Inherit from `Test`.
- Create a `setUp()` function.
- Create a function `testFuzz_...` that takes arguments (fuzz inputs).
- Define the invariant property that should HOLD (e.g., balance >= 0).
- Use `assert` or `vm.assume` as needed.
- Ensure complete compilable code.
"""),
            ("user", """Target Contract:
```solidity
{source_code}
```

Invariant to Check:
{property_desc}

Generate Fuzz Test:""")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            response = chain.invoke({
                "source_code": source_code,
                "property_desc": property_desc
            })
            response = response.replace("```solidity", "").replace("```", "").strip()
            return response
        except Exception as e:
            logger.error(f"Fuzz test generation failed: {e}")
            return ""
