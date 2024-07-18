# This is a sample Python file

def greet(name):
    """
    A simple function to greet a person
    """
    return f"Hello, {name}! Welcome to Python programming."

def calculate_sum(a, b):
    """
    A function to calculate the sum of two numbers
    """
    return a + b

if __name__ == "__main__":
    # Example usage of the functions
    print(greet("Alice"))
    result = calculate_sum(5, 7)
    print(f"The sum of 5 and 7 is: {result}")