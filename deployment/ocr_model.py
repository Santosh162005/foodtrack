import cv2
import pytesseract
import re
from datetime import datetime
import numpy as np

# Configure Tesseract path (update this based on your installation)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class ExpiryDateExtractor:
    def __init__(self):
        self.date_patterns = [
            r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b',  # DD/MM/YYYY or DD-MM-YYYY
            r'\b(\d{2,4})[/-](\d{1,2})[/-](\d{1,2})\b',  # YYYY/MM/DD or YYYY-MM-DD
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2})[,\s]+(\d{2,4})\b',  # Month DD, YYYY
            r'\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{2,4})\b',  # DD Month YYYY
            r'\b(EXP|Exp|exp|EXPIRY|Expiry)[:\s]+(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b',  # EXP: DD/MM/YYYY
            r'\b(BEST BEFORE|Best Before|USE BY|Use By)[:\s]+(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b',  # Best Before: DD/MM/YYYY
            r'\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b',  # DD.MM.YYYY
        ]
        
        self.month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
    
    def preprocess_image(self, image_path):
        """Preprocess image for better OCR accuracy"""
        # Read image
        img = cv2.imread(image_path)
        
        if img is None:
            raise ValueError("Unable to read image")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Noise removal
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        
        # Morphological operations
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.dilate(denoised, kernel, iterations=1)
        processed = cv2.erode(processed, kernel, iterations=1)
        
        # Increase contrast
        processed = cv2.convertScaleAbs(processed, alpha=1.5, beta=0)
        
        return img, processed
    
    def extract_text(self, image_path):
        """Extract text from image using Tesseract OCR"""
        try:
            original, processed = self.preprocess_image(image_path)
            
            # Try with different PSM modes for better accuracy
            custom_config = r'--oem 3 --psm 6'
            text1 = pytesseract.image_to_string(processed, config=custom_config)
            
            custom_config = r'--oem 3 --psm 11'
            text2 = pytesseract.image_to_string(processed, config=custom_config)
            
            # Combine texts
            text = text1 + "\n" + text2
            
            return text
        except Exception as e:
            print(f"Error in OCR extraction: {str(e)}")
            return ""
    
    def parse_date(self, date_string):
        """Parse various date formats"""
        # Clean the string
        date_string = date_string.strip()
        
        # Try different date formats
        formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
            '%Y/%m/%d', '%Y-%m-%d',
            '%d/%m/%y', '%d-%m-%y', '%d.%m.%y',
            '%y/%m/%d', '%y-%m-%d',
            '%d %B %Y', '%d %b %Y',
            '%B %d, %Y', '%b %d, %Y'
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_string, fmt)
                # Convert 2-digit year to 4-digit
                if parsed_date.year < 100:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    def extract_expiry_date(self, image_path):
        """Main function to extract expiry date from image"""
        text = self.extract_text(image_path)
        
        if not text:
            return None, "Could not extract text from image"
        
        dates_found = []
        
        # Search for date patterns
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                
                # Handle different pattern types
                if len(groups) >= 3:
                    # Skip prefix words like EXP, BEST BEFORE
                    if groups[0].lower() in ['exp', 'expiry', 'best before', 'use by']:
                        groups = groups[1:]
                    
                    # Check if first group is a month name
                    if groups[0].lower()[:3] in self.month_map:
                        month = self.month_map[groups[0].lower()[:3]]
                        day = int(groups[1])
                        year = int(groups[2])
                        date_str = f"{day:02d}/{month:02d}/{year}"
                    elif groups[1].lower()[:3] in self.month_map:
                        day = int(groups[0])
                        month = self.month_map[groups[1].lower()[:3]]
                        year = int(groups[2])
                        date_str = f"{day:02d}/{month:02d}/{year}"
                    else:
                        date_str = f"{groups[0]}/{groups[1]}/{groups[2]}"
                    
                    parsed = self.parse_date(date_str)
                    if parsed:
                        dates_found.append(parsed)
        
        if dates_found:
            # Return the first valid date found
            return dates_found[0], text
        
        return None, text
    
    def extract_food_name(self, text):
        """Extract potential food name from text (basic implementation)"""
        lines = text.split('\n')
        # Usually product name is in first few lines and has certain characteristics
        for line in lines[:5]:
            line = line.strip()
            # Skip very short lines and lines that look like dates or numbers
            if len(line) > 3 and not re.match(r'^[\d\s/\-\.]+$', line):
                # Clean up the line
                cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', line)
                if len(cleaned) > 3:
                    return cleaned.strip()
        return "Unknown"


# Test function
if __name__ == "__main__":
    extractor = ExpiryDateExtractor()
    
    # Test with sample image
    test_image = "static/uploads/test.jpg"
    try:
        expiry_date, extracted_text = extractor.extract_expiry_date(test_image)
        food_name = extractor.extract_food_name(extracted_text)
        
        print("Extracted Text:")
        print(extracted_text)
        print("\n" + "="*50)
        print(f"Food Name: {food_name}")
        print(f"Expiry Date: {expiry_date}")
    except Exception as e:
        print(f"Error: {str(e)}")
