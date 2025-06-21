#!/usr/bin/env python3
"""
Test script for the standalone PDF Generator app
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
django.setup()

from pdf_generator.core.generator import PDFGenerator

def test_standalone_pdf_generator():
    """Test the standalone PDF generator app"""
    
    print("🧪 Testing Standalone PDF Generator App")
    print("=" * 50)
    
    # Test 1: Generate PDF from template
    print("\n1. Testing PDF generation from template...")
    try:
        context = {
            'title': 'Standalone PDF Generator Test',
            'subtitle': 'Testing the new standalone app',
            'date': '2024-01-01',
            'content': '''
                <h2>Test Results</h2>
                <p>This PDF was generated using the standalone PDF Generator app.</p>
                <ul>
                    <li>✅ App is working correctly</li>
                    <li>✅ Template rendering works</li>
                    <li>✅ PDF generation successful</li>
                    <li>✅ Standalone functionality confirmed</li>
                </ul>
            '''
        }
        
        pdf_bytes = PDFGenerator.generate_from_template(
            template_name='pdf_generator/default.html',
            context=context,
            options={'format': 'A4', 'print_background': True}
        )
        
        # Save test PDF
        file_path = PDFGenerator.save_to_file(pdf_bytes, 'standalone_test.pdf')
        
        print(f"✅ PDF generated successfully!")
        print(f"📄 File saved as: {file_path}")
        print(f"📊 File size: {len(pdf_bytes)} bytes")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 2: Generate PDF from HTML
    print("\n2. Testing PDF generation from HTML...")
    try:
        html_content = """
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h1>HTML Content Test</h1>
            <p>This PDF was generated from raw HTML content.</p>
            <ul>
                <li>Direct HTML input</li>
                <li>Custom styling</li>
                <li>No template required</li>
            </ul>
        </div>
        """
        
        pdf_bytes = PDFGenerator.generate_from_html(
            html_content=html_content,
            options={'format': 'A4', 'print_background': True}
        )
        
        file_path = PDFGenerator.save_to_file(pdf_bytes, 'html_test.pdf')
        
        print(f"✅ HTML to PDF successful!")
        print(f"📄 File saved as: {file_path}")
        print(f"📊 File size: {len(pdf_bytes)} bytes")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 3: Test different options
    print("\n3. Testing different PDF options...")
    try:
        context = {
            'title': 'Options Test',
            'content': '<p>Testing different PDF generation options.</p>'
        }
        
        options = {
            'format': 'Letter',
            'orientation': 'portrait',
            'margins': {
                'top': '0.25in',
                'right': '0.25in',
                'bottom': '0.25in',
                'left': '0.25in'
            },
            'print_background': True
        }
        
        pdf_bytes = PDFGenerator.generate_from_template(
            template_name='pdf_generator/default.html',
            context=context,
            options=options
        )
        
        file_path = PDFGenerator.save_to_file(pdf_bytes, 'options_test.pdf')
        
        print(f"✅ Custom options test successful!")
        print(f"📄 File saved as: {file_path}")
        print(f"📊 File size: {len(pdf_bytes)} bytes")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Standalone PDF Generator is working correctly.")
    print("\n📋 Summary:")
    print("✅ Template-based PDF generation")
    print("✅ HTML-to-PDF conversion")
    print("✅ Custom options support")
    print("✅ File saving functionality")
    print("✅ Standalone app architecture")
    
    return True

if __name__ == "__main__":
    success = test_standalone_pdf_generator()
    sys.exit(0 if success else 1) 