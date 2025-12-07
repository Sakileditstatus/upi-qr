from flask import Flask, request, send_file, jsonify
import qrcode
from PIL import Image
import io
import os
from datetime import datetime

app = Flask(__name__)

@app.route("/generate", methods=["GET"])
def generate_qr():
    try:
        # ============================
        # Get URL parameters
        # ============================
        upi_id = request.args.get("upi_id")
        amount = request.args.get("amount", "")
        size = int(request.args.get("size", 1024))
        box_size = int(request.args.get("box_size", 10))
        border = int(request.args.get("border", 4))
        fill_color = request.args.get("fill", "black")
        qr_format = request.args.get("format", "png").lower()
        save = request.args.get("save", "false").lower() == "true"
        save_dir = request.args.get("dir", "qr_codes")

        if not upi_id:
            return jsonify({"error": "upi_id parameter is required"}), 400

        # ============================
        # Create UPI URL
        # ============================
        upi_link = f"upi://pay?pa={upi_id}"
        if amount:
            upi_link += f"&am={amount}"

        # ============================
        # QR Code Generation
        # ============================
        qr = qrcode.QRCode(
            version=1,
            box_size=box_size,
            border=border
        )
        qr.add_data(upi_link)
        qr.make(fit=True)

        # BG color removed → always white
        img = qr.make_image(fill_color=fill_color, back_color="white").convert("RGB")

        # Resize final QR
        img = img.resize((size, size), Image.NEAREST)

        # ============================
        # Save to memory
        # ============================
        img_bytes = io.BytesIO()
        img.save(img_bytes, format=qr_format.upper())
        img_bytes.seek(0)

        # ============================
        # Save to server if requested
        # ============================
        saved_path = None
        if save:
            os.makedirs(save_dir, exist_ok=True)
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"qr_{upi_id.replace('@','_')}_{amount}_{now}.{qr_format}"
            saved_path = os.path.join(save_dir, file_name)
            img.save(saved_path)

        # ============================
        # Return file or path
        # ============================
        if save:
            return jsonify({
                "status": "saved",
                "file": saved_path.replace("\\", "/")
            })

        return send_file(img_bytes, mimetype=f"image/{qr_format}")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
