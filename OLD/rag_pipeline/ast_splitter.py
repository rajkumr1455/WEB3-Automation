import os
from tree_sitter import Language, Parser
import tree_sitter_solidity

class ASTSplitter:
    def __init__(self):
        self.parser = Parser()
        # Load Solidity language
        # In newer tree-sitter versions, we might need to load it differently
        # Assuming tree_sitter_solidity provides the language object
        try:
            SOL_LANG = Language(tree_sitter_solidity.language())
            self.parser.set_language(SOL_LANG)
        except Exception as e:
            print(f"Error loading tree-sitter language: {e}")
            self.parser = None

    def extract_functions(self, source_code: str) -> list[str]:
        """
        Parses the source code and extracts complete function bodies.
        """
        if not self.parser:
            return [source_code] # Fallback

        tree = self.parser.parse(bytes(source_code, "utf8"))
        root_node = tree.root_node
        
        functions = []
        
        # Traverse the tree to find function definitions
        # This is a simplified traversal
        cursor = tree.walk()
        
        visited_children = False
        while True:
            if not visited_children:
                if cursor.node.type == 'function_definition':
                    # Extract the full text of the function
                    start_byte = cursor.node.start_byte
                    end_byte = cursor.node.end_byte
                    func_text = source_code.encode('utf8')[start_byte:end_byte].decode('utf8')
                    functions.append(func_text)
                    # Don't visit children of a function definition to avoid partials
                    # But we might want modifiers? 
                    # For RAG, the whole function body is good.
            
            if cursor.goto_first_child():
                visited_children = False
            elif cursor.goto_next_sibling():
                visited_children = False
            elif cursor.goto_parent():
                visited_children = True
            else:
                break
                
        return functions

if __name__ == "__main__":
    splitter = ASTSplitter()
    code = """
    contract Test {
        function foo() public {
            // comment
            uint x = 1;
        }
        
        function bar() external returns (bool) {
            return true;
        }
    }
    """
    funcs = splitter.extract_functions(code)
    for f in funcs:
        print("-" * 20)
        print(f)
