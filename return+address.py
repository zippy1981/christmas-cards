from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import csv

def create_avery_5160_labels(output_file, return_address):
    # Dimensions of Avery 5160 labels
    page_width, page_height = letter
    label_width = 2.625 * inch
    label_height = 1.0 * inch
    margin_x = 0.1875 * inch
    margin_y = 0.5 * inch
    spacing_x = 0.125 * inch
    spacing_y = 0.0 * inch

    # Font settings
    font_name = "Helvetica"
    font_size = 10

    # Create a PDF canvas
    c = canvas.Canvas(output_file, pagesize=letter)

    # Function to draw full-length tick marks
    def draw_tick_marks():
        middle_x = page_width / 2
        middle_y = page_height / 2

        # Horizontal tick mark (entire width of the page)
        c.line(0, middle_y, page_width, middle_y)

        # Vertical tick mark (entire height of the page)
        c.line(middle_x, 0, middle_x, page_height)

    # Coordinates for labels
    x_start = margin_x
    y_start = page_height - margin_y - label_height
    x = x_start
    y = y_start

    count = 0
    for _ in range(30):  # Avery 5160 has 30 labels per page
        # Draw the page border and tick marks if starting a new page
        if count % 30 == 0:  # New page
            if count > 0:  # Close the previous page
                c.showPage()
        
        # Draw the return address inside the label
        c.setFont(font_name, font_size)
        text_x = x + 0.1 * inch
        text_y = y + 0.8 * inch
        for line in return_address.split("\n"):
            c.drawString(text_x, text_y, line)
            text_y -= 0.13 * inch  # Line spacing

        # Move to the next label position
        count += 1
        if count % 3 == 0:  # New row
            x = x_start
            y -= (label_height + spacing_y)
        else:  # Move to the next column
            x += (label_width + spacing_x)

    # Save the PDF
    c.save()

if __name__ == "__main__":
    # Replace this with your desired return address
    return_address = """Justin and Dr Ma Lucille Dearing
219 Scherrer Street
Cranford, NJ 07016"""

    # Output file path
    output_pdf = "avery_5160_return_addresses.pdf"

    create_avery_5160_labels(output_pdf, return_address)
