import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import requests
import json
import pyautogui
import pyperclip
from pynput import keyboard
import re
from PIL import Image, ImageGrab
import pytesseract
import cv2
import numpy as np
import sys

class ClaudeAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
    
    def validate_api_key(self):
        """Test if the API key is valid"""
        try:
            data = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 10,
                "messages": [
                    {"role": "user", "content": "Hi"}
                ]
            }
            
            response = requests.post(self.base_url, headers=self.headers, json=data)
            return response.status_code == 200
            
        except Exception as e:
            print(f"API validation error: {e}")
            return False
    
    def generate_hint(self, problem_description, current_code, problem_title=""):
        # Create a fallback prompt if OCR failed
        if not problem_description.strip() or "could not extract" in problem_description.lower():
            prompt = f"""
            You are a coding mentor. The user is working on a LeetCode problem but I couldn't extract the problem description from their screen.
            
            Current Code:
            {current_code}
            
            Based on their code, please provide:
            1. What type of problem this appears to be (array, string, tree, etc.)
            2. Potential approaches they might consider
            3. Common patterns that might apply
            4. Ask them to share the problem details for more specific help
            
            Keep the response helpful and encouraging (under 200 words).
            """
        else:
            prompt = f"""
            You are a coding mentor helping with LeetCode problems. The user is working on: {problem_title}
            
            Problem Description:
            {problem_description}
            
            Current Code:
            {current_code}
            
            Please provide a helpful hint or example that guides them toward the solution pattern without giving away the complete answer. Focus on:
            1. A concrete example that illustrates the pattern
            2. Key insights about the approach
            3. Common pitfalls to avoid
            
            Keep the response concise and actionable (under 200 words).
            """
        
        try:
            data = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 300,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            print(f"Making API request to: {self.base_url}")
            
            response = requests.post(self.base_url, headers=self.headers, json=data)
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Response content: {response.text}")
                
                # Try with different model names
                for model_name in ["claude-3-sonnet-20240229", "claude-sonnet-4-20250514"]:
                    print(f"Trying with model: {model_name}")
                    data["model"] = model_name
                    response = requests.post(self.base_url, headers=self.headers, json=data)
                    if response.status_code == 200:
                        break
            
            response.raise_for_status()
            
            result = response.json()
            return result['content'][0]['text']
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response text: {e.response.text}")
            return f"API Error: {str(e)}"
        except Exception as e:
            print(f"Unexpected error: {e}")
            return f"Error generating hint: {str(e)}"

class LeetCodeScraper:
    def __init__(self):
        # Try to set up tesseract path (common Windows installation)
        try:
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        except:
            pass  # Will work if tesseract is in PATH
    
    def capture_screen_region(self, region=None):
        """Capture screen or specific region"""
        if region:
            screenshot = ImageGrab.grab(bbox=region)
        else:
            screenshot = ImageGrab.grab()
        return screenshot
    
    def preprocess_image_for_ocr(self, image):
        """Preprocess image for better OCR results"""
        # Convert PIL image to OpenCV format
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get better contrast
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Convert back to PIL
        return Image.fromarray(thresh)
    
    def extract_text_from_image(self, image):
        """Extract text from image using OCR"""
        try:
            # Try different OCR configurations for better results
            configs = [
                '--psm 6',  # Uniform block of text
                '--psm 4',  # Single column of text
                '--psm 3',  # Fully automatic page segmentation
                '--psm 1'   # Automatic page segmentation with OSD
            ]
            
            for config in configs:
                try:
                    # Preprocess image
                    processed_image = self.preprocess_image_for_ocr(image)
                    
                    # Extract text
                    text = pytesseract.image_to_string(processed_image, config=config)
                    
                    if text.strip():  # If we got some text, use it
                        return text.strip()
                        
                except Exception as e:
                    print(f"OCR config {config} failed: {e}")
                    continue
            
            # If all configs failed, try with original image
            text = pytesseract.image_to_string(image, config='--psm 6')
            return text.strip()
            
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""
    
    def get_problem_info(self):
        """Extract problem information from screen"""
        try:
            # Get screen dimensions
            screen_width, screen_height = pyautogui.size()
            print(f"Screen dimensions: {screen_width}x{screen_height}")
            
            # Capture left side of screen where problem description usually is
            problem_region = (0, 0, screen_width // 2, screen_height)
            print(f"Capturing problem region: {problem_region}")
            
            screenshot = self.capture_screen_region(problem_region)
            
            # Save debug image
            screenshot.save("debug_problem_area.png")
            print("Saved debug image: debug_problem_area.png")
            
            # Extract text from the problem area
            problem_text = self.extract_text_from_image(screenshot)
            print(f"Raw extracted text length: {len(problem_text)}")
            print(f"First 200 chars: {problem_text[:200]}")
            
            if not problem_text.strip():
                return "No Problem Detected", "Could not extract text from screen. Make sure LeetCode is visible and try again."
            
            # Try to extract problem title (usually at the top)
            lines = problem_text.split('\n')
            title = "LeetCode Problem"
            description = problem_text
            
            # Look for typical LeetCode problem patterns
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in ['given', 'return', 'find', 'calculate', 'implement', 'design']):
                    if i > 0:
                        # Look for a title in previous lines
                        for j in range(max(0, i-5), i):
                            if lines[j].strip() and len(lines[j]) < 100:
                                title = lines[j].strip()
                                break
                    break
            
            # Also look for numbered problems (e.g., "1. Two Sum")
            for line in lines[:10]:  # Check first 10 lines
                if re.match(r'^\d+\.\s+', line.strip()):
                    title = line.strip()
                    break
            
            # Clean up the description
            description = self.clean_problem_text(problem_text)
            
            print(f"Extracted title: {title}")
            print(f"Description length: {len(description)}")
            
            return title, description
            
        except Exception as e:
            print(f"Error extracting problem info: {e}")
            return "Error", f"Could not extract problem from screen: {str(e)}"
    
    def get_current_code(self):
        """Extract current code from the code editor area"""
        try:
            # Get screen dimensions
            screen_width, screen_height = pyautogui.size()
            
            # Capture right side of screen where code editor usually is
            code_region = (screen_width // 2, 0, screen_width, screen_height)
            print(f"Capturing code region: {code_region}")
            
            screenshot = self.capture_screen_region(code_region)
            
            # Save debug image
            screenshot.save("debug_code_area.png")
            print("Saved debug image: debug_code_area.png")
            
            # Extract text from code area
            code_text = self.extract_text_from_image(screenshot)
            print(f"Raw code text length: {len(code_text)}")
            print(f"First 200 chars: {code_text[:200]}")
            
            # Clean up the code text
            code = self.clean_code_text(code_text)
            
            return code if code.strip() else "No code written yet"
            
        except Exception as e:
            print(f"Error extracting code: {e}")
            return f"Could not extract current code: {str(e)}"
    
    def clean_problem_text(self, text):
        """Clean and format problem description text"""
        # Remove extra whitespace and line breaks
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Filter out navigation elements and UI text
        filtered_lines = []
        skip_keywords = ['leetcode', 'premium', 'subscribe', 'difficulty', 'acceptance', 'submissions', 'runtime', 'memory']
        
        for line in lines:
            if not any(keyword in line.lower() for keyword in skip_keywords):
                # Keep lines that look like problem content
                if len(line) > 3 and not line.isdigit():
                    filtered_lines.append(line)
        
        result = '\n'.join(filtered_lines)
        print(f"Cleaned problem text: {result[:300]}...")
        return result
    
    def clean_code_text(self, text):
        """Clean and format extracted code text"""
        # Remove line numbers if present
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove line numbers (pattern: digits at start of line)
            cleaned_line = re.sub(r'^\d+\s*', '', line)
            if cleaned_line.strip():
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)
    
    def close(self):
        """No cleanup needed for screen capture approach"""
        pass

class HinterviewOverlay:
    def __init__(self, claude_api):
        self.claude_api = claude_api
        self.scraper = LeetCodeScraper()
        self.root = None
        self.overlay_visible = False
        self.setup_ui()
        self.setup_hotkey()
        
    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("Hinterview")
        self.root.geometry("400x300")
        
        # Make window transparent and always on top
        self.root.attributes('-alpha', 0.9)
        self.root.attributes('-topmost', True)
        
        # Position window in top-right corner
        self.root.geometry("+{}+{}".format(
            self.root.winfo_screenwidth() - 420, 50
        ))
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title label
        self.title_label = ttk.Label(main_frame, text="Hinterview",
                                   font=("Arial", 14, "bold"))
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Press F1 for hint",
                                    font=("Arial", 10))
        self.status_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # Hint display area
        self.hint_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD,
                                                 height=12, width=45)
        self.hint_text.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        self.generate_btn = ttk.Button(button_frame, text="Generate Hint",
                                     command=self.generate_hint)
        self.generate_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.close_btn = ttk.Button(button_frame, text="Close",
                                  command=self.toggle_overlay)
        self.close_btn.grid(row=0, column=1, padx=(5, 0))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Hide initially
        self.root.withdraw()
        
    def setup_hotkey(self):
        def on_hotkey():
            self.toggle_overlay()
        
        # Set up F1 hotkey
        self.hotkey_listener = keyboard.GlobalHotKeys({
            '<f1>': on_hotkey
        })
        self.hotkey_listener.start()
    
    def toggle_overlay(self):
        if self.overlay_visible:
            self.root.withdraw()
            self.overlay_visible = False
        else:
            self.root.deiconify()
            self.overlay_visible = True
            self.generate_hint()
    
    def generate_hint(self):
        def generate_in_thread():
            try:
                self.status_label.config(text="Generating hint...")
                self.hint_text.delete(1.0, tk.END)
                self.hint_text.insert(tk.END, "Analyzing problem and your code...")
                
                # Get problem info and current code
                problem_title, problem_description = self.scraper.get_problem_info()
                current_code = self.scraper.get_current_code()
                
                # Generate hint using Claude
                hint = self.claude_api.generate_hint(
                    problem_description, current_code, problem_title
                )
                
                # Display hint
                self.hint_text.delete(1.0, tk.END)
                self.hint_text.insert(tk.END, hint)
                self.status_label.config(text=f"Hint for: {problem_title}")
                
            except Exception as e:
                self.hint_text.delete(1.0, tk.END)
                self.hint_text.insert(tk.END, f"Error: {str(e)}")
                self.status_label.config(text="Error generating hint")
        
        # Run in separate thread to avoid blocking UI
        threading.Thread(target=generate_in_thread, daemon=True).start()
    
    def run(self):
        try:
            print("Hinterview is running... Press F1 for hints!")
            print("Press Ctrl+C to exit")
            self.root.mainloop()
        except KeyboardInterrupt:
            self.cleanup()
    
    def cleanup(self):
        if hasattr(self, 'hotkey_listener'):
            self.hotkey_listener.stop()
        self.scraper.close()
        if self.root:
            self.root.destroy()

def main():
    # Get API key from user
    api_key = input("Enter your Claude API key: ").strip()
    
    if not api_key:
        print("API key is required!")
        return
    
    # Initialize and validate API
    claude_api = ClaudeAPI(api_key)
    print("Validating API key...")
    
    if not claude_api.validate_api_key():
        print("Invalid API key or API error. Please check your key and try again.")
        return
    
    print("API key validated successfully!")
    
    # Initialize app
    app = HinterviewOverlay(claude_api)
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down Hinterview...")
        app.cleanup()

if __name__ == "__main__":
    main()
