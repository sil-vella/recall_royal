import re
import os
from typing import Dict, List, Union

class PasswordPolicy:
    """Handles password validation and strength scoring."""

    def __init__(self):
        """Initialize password policy with configurable requirements."""
        self.min_length = int(os.getenv("PASSWORD_MIN_LENGTH", "12"))
        self.max_length = int(os.getenv("PASSWORD_MAX_LENGTH", "128"))
        self.min_uppercase = int(os.getenv("PASSWORD_MIN_UPPERCASE", "1"))
        self.min_lowercase = int(os.getenv("PASSWORD_MIN_LOWERCASE", "1"))
        self.min_digits = int(os.getenv("PASSWORD_MIN_DIGITS", "1"))
        self.min_special = int(os.getenv("PASSWORD_MIN_SPECIAL", "1"))
        self.max_repeated_chars = int(os.getenv("PASSWORD_MAX_REPEATED_CHARS", "3"))
        
        # Common password list (should be loaded from a file in production)
        self.common_passwords = {
            "password", "123456", "qwerty", "admin", "letmein",
            "welcome", "monkey", "password123", "abc123", "test123"
        }

    def validate_password(self, password: str) -> Dict[str, Union[bool, List[str]]]:
        """
        Validate a password against all policy requirements.
        
        Returns:
            Dict containing:
                - valid (bool): Whether the password meets all requirements
                - errors (List[str]): List of validation errors if any
                - strength (int): Password strength score (0-100)
        """
        errors = []
        
        # Check length
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        if len(password) > self.max_length:
            errors.append(f"Password cannot be longer than {self.max_length} characters")
            
        # Check character types
        if sum(1 for c in password if c.isupper()) < self.min_uppercase:
            errors.append(f"Password must contain at least {self.min_uppercase} uppercase letter(s)")
        if sum(1 for c in password if c.islower()) < self.min_lowercase:
            errors.append(f"Password must contain at least {self.min_lowercase} lowercase letter(s)")
        if sum(1 for c in password if c.isdigit()) < self.min_digits:
            errors.append(f"Password must contain at least {self.min_digits} number(s)")
        if sum(1 for c in password if not c.isalnum()) < self.min_special:
            errors.append(f"Password must contain at least {self.min_special} special character(s)")
            
        # Check for common passwords
        if password.lower() in self.common_passwords:
            errors.append("Password is too common")
            
        # Check for repeated characters
        for i in range(len(password) - self.max_repeated_chars + 1):
            if len(set(password[i:i + self.max_repeated_chars])) == 1:
                errors.append(f"Password cannot contain more than {self.max_repeated_chars} repeated characters")
                break
                
        # Check for sequential characters
        if self._has_sequential_chars(password):
            errors.append("Password cannot contain sequential characters (e.g., '123', 'abc')")
            
        # Calculate strength score
        strength = self._calculate_strength(password)
            
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength": strength
        }
        
    def _has_sequential_chars(self, password: str) -> bool:
        """Check if password contains sequential characters."""
        sequences = [
            "abcdefghijklmnopqrstuvwxyz",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "0123456789"
        ]
        
        for seq in sequences:
            for i in range(len(seq) - 2):
                if seq[i:i+3] in password:
                    return True
        return False
        
    def _calculate_strength(self, password: str) -> int:
        """
        Calculate password strength score (0-100).
        
        Factors considered:
        - Length
        - Character variety
        - Special characters
        - Numbers
        - Case mixing
        - Non-sequential characters
        """
        score = 0
        
        # Length score (up to 25 points)
        length_score = min(len(password) / self.max_length * 25, 25)
        score += length_score
        
        # Character variety score (up to 25 points)
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        variety_score = sum([has_upper, has_lower, has_digit, has_special]) * 6.25
        score += variety_score
        
        # Unique characters score (up to 25 points)
        unique_ratio = len(set(password)) / len(password)
        score += unique_ratio * 25
        
        # Complexity patterns score (up to 25 points)
        complexity_score = 25
        
        if self._has_sequential_chars(password):
            complexity_score -= 10
            
        if password.lower() in self.common_passwords:
            complexity_score -= 15
            
        for i in range(len(password) - 2):
            if len(set(password[i:i+3])) == 1:
                complexity_score -= 5
                break
                
        score += max(complexity_score, 0)
        
        return min(round(score), 100) 