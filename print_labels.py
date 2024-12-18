from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import csv

def create_avery_5160_labels(csv_file, output_file):
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

    def draw_tick_marks():
        middle_x = page_width / 2
        middle_y = page_height / 2
        tick_length = 0.5 * inch  # Length of the tick marks

        # Horizontal tick mark
        c.line(middle_x - tick_length / 2, middle_y, middle_x + tick_length / 2, middle_y)

        # Vertical tick mark
        c.line(middle_x, middle_y - tick_length / 2, middle_x, middle_y + tick_length / 2)


    # Read the CSV file
    with open(csv_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        headers = next(reader)  # Skip the header row

        # Add a border around the entire document
        border_thickness = 2  # Set border thickness (2px ~ 0.0276 inch)
        c.setLineWidth(border_thickness / 72 * inch)  # Convert px to points
        c.rect(
            0,  # Left margin
            0,  # Bottom margin
            page_width - 2,  # Width of the border
            page_height - 2,  # Height of the border
            stroke=1,
            fill=0,
        )

        # Coordinates for labels
        x_start = margin_x
        y_start = page_height - margin_y - label_height
        x = x_start
        y = y_start

        count = 0
        for row in reader:
            # Format the address

            # Draw the border for the label
            #border_thickness = 1  # Set border thickness (1px ~ 0.0138 inch)
            #c.setLineWidth(border_thickness / 72 * inch)  # Convert px to points
            #c.rect(x, y, label_width, label_height, stroke=1, fill=0)
            

            # Draw the address on the label
            c.setFont(font_name, font_size)
            textObject = c.beginText(x + 0.1 * inch, y + 0.6 * inch)
            textObject.textLine(f"{row['First Name']} {row['Last Name']}")
            textObject.textLine(f"{row['streetNumber']} {row['streetName']}")
            textObject.textLine(f"{row['municipality']}, {row['countrySubdivision']} {row['extendedPostalCode']}")
            c.drawText(textObject)

            # Move to the next label position
            count += 1
            if count % 3 == 0:  # New row
                x = x_start
                y -= (label_height + spacing_y)
            else:  # Move to the next column
                x += (label_width + spacing_x)

            # Check if the page is full
            if count % 30 == 0:  # New page
                #draw_tick_marks()
                c.showPage()
                x = x_start
                y = y_start
        #draw_tick_marks()

    # Save the PDF
    c.save()

if __name__ == "__main__":
    # Replace these with your actual file paths
    input_csv = "For Labels.csv"  # Input CSV file
    output_pdf = "avery_5160_labels.pdf"  # Output PDF file

    create_avery_5160_labels(input_csv, output_pdf)
