// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";

contract Test {
    uint256 public balance;

    function deposit() external payable {
        balance += msg.value;
    }

    function withdraw(uint256 _amount) external {
        require(balance >= _amount, "Insufficient balance");
        payable(msg.sender).transfer(_amount);
        balance -= _amount;
    }
}

contract ReentrancyExploit is Test {
    Test test;

    constructor(address _testAddress) {
        test = Test(_testAddress);
    }

    receive() external payable {}

    function exploit(uint256 _initialDeposit, uint256 _withdrawAmount) public payable {
        require(msg.value == _initialDeposit, "Initial deposit must match");
        test.deposit{value: _initialDeposit}();
        test.withdraw(_withdrawAmount);
    }
}

contract ReentrancyTest is Test {
    Test test;
    ReentrancyExploit exploit;

    function setUp() public {
        test = new Test();
        exploit = new ReentrancyExploit(address(test));
    }

    function testReentrancyExploit() public {
        uint256 initialDeposit = 1 ether;
        uint256 withdrawAmount = 0.9 ether;

        // Deploy the attacker contract and initiate the exploit
        (bool success, ) = address(exploit).call{value: initialDeposit}(
            abi.encodeWithSignature("exploit(uint256,uint256)", initialDeposit, withdrawAmount)
        );
        require(success, "Exploit call failed");

        // Assert that the attacker has stolen funds
        assertEq(address(test).balance, 0.1 ether);
    }
}