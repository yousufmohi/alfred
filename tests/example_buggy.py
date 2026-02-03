"""
Example buggy code for testing Alfred
This intentionally has several issues!
"""

import os

def calculate_average(numbers):
    # Bug: Division by zero if list is empty
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)


def fetch_user_data(user_id):
    # Security issue: SQL injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    # Simulated database call
    print(f"Executing: {query}")
    return {"id": user_id, "name": "John"}


class UserManager:
    def __init__(self):
        self.users = []
    
    # Bug: Mutable default argument
    def add_users(self, new_users=[]):
        self.users.extend(new_users)
        return self.users
    
    # Performance issue: Nested loops with poor complexity
    def find_duplicates(self):
        duplicates = []
        for i in range(len(self.users)):
            for j in range(len(self.users)):
                if i != j and self.users[i] == self.users[j]:
                    duplicates.append(self.users[i])
        return duplicates


def process_file(filename):
    # Bug: File handle not properly closed
    file = open(filename, 'r')
    content = file.read()
    # Missing file.close()
    return content


# Bug: Using except without specifying exception type
def risky_operation():
    try:
        result = 10 / 0
        return result
    except:
        pass
    

# Style issue: Poor naming and no docstrings
def f(x, y):
    return x + y


if __name__ == "__main__":
    # Bug: Potential IndexError
    numbers = []
    print(calculate_average(numbers))
    
    # Security issue being called
    user = fetch_user_data("1 OR 1=1")
    print(user)