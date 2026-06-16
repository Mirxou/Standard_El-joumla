import os

import qrcode


class QRCodeService:
    """
    The 'Digital Twin' Generator: Links physical objects to digital records.
    """

    def __init__(self):
        self.output_dir = "temp_qrcodes"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_digital_twin(self, doc_type, doc_id):
        """
        Generates a QR code containing a deep link to the object.
        Example: erp://product/55
        """
        deep_link = f"erp://{doc_type}/{doc_id}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(deep_link)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        filename = f"{self.output_dir}/{doc_type}_{doc_id}.png"
        img.save(filename)
        return os.path.abspath(filename), deep_link
