from PyPDF2 import PdfReader


def correct_eof_error_in_pdf(file_path:str) -> None:
    """
    Corrects the EOF error in downloaded PDFs
    Params:
    @file_path: Path to the pdf to be processed
    """
    with open(file_path, 'rb') as p:
        txt = (p.readlines())

    # Function to dealing with EOF error in pdf's
    def reset_eof_of_pdf_return_stream(pdf_stream_in: list):
        # find the line position of the EOF
        actual_line = 0
        for i, x in enumerate(txt[::-1]):
            if b'%%EOF' in x:
                actual_line = len(pdf_stream_in) - i
                # print(f'EOF found at line position {-i} = actual {actual_line}, with value {x}')
                break

        # return the list up to that point
        return pdf_stream_in[:actual_line]

    # get the new list terminating correctly
    txtx = reset_eof_of_pdf_return_stream(txt)
    # write to new pdf
    with open(file_path, 'wb') as f:
        f.writelines(txtx)


def extract_content_from_pdf(file_path: str) -> list[str]:
    reader = PdfReader(file_path)

    content = []
    for i in range(len(reader.pages)):
        page_content = reader.pages[i].extract_text().strip()
        if len(page_content) > 0:
            content.append(page_content)
    return content

