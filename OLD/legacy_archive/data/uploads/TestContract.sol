// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleVulnerableContract {
    address public owner;
    mapping(address => uint256) public balances;
    
    constructor() {
        owner = msg.sender;
    }
    
    // Vulnerability: Missing access control
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        // Vulnerability: Reentrancy
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] -= amount;
    }
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
    
    // Vulnerability: tx.origin for authentication
    function emergencyWithdraw() public {
        require(tx.origin == owner, "Not owner");
        payable(owner).transfer(address(this).balance);
    }
}
