from slither_wrapper import SlitherWrapper
import sys
import os

def test():
    print(f"Python Executable: {sys.executable}")
    wrapper = SlitherWrapper()
    # Create a dummy file if not exists
    if not os.path.exists("Target.sol"):
        with open("Target.sol", "w") as f:
            f.write("pragma solidity ^0.8.0; contract Test {}")
            
    print("Running SlitherWrapper...")
    results = wrapper.run("Target.sol")
    print("Results:", results)

if __name__ == "__main__":
    test()
