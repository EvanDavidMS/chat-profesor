from flask import Flask, request, jsonify, send_from_directory, render_template_string
import os, requests
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["https://chat-profesor.onrender.com/"])  # Aquí pones la URL de tu servidor de alumno
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

mensajes = []

# URL pública del servidor Alumno (configurada mediante variable de entorno)
TARGET_ALUMNO_URL = os.environ.get("TARGET_ALUMNO_URL", "https://chat-profesor.onrender.com/")

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Chat - Profesor</title>
      <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
      <style>
         body {
             font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
             background: linear-gradient(135deg, #f0f0f0, #cfcfcf);
             display: flex;
             justify-content: center;
             align-items: center;
             height: 100vh;
             margin: 0;
         }
         .chat-container {
             background: #fff;
             padding: 20px;
             border-radius: 10px;
             box-shadow: 0 4px 15px rgba(0,0,0,0.2);
             width: 400px;
         }
         h1, h2 { text-align: center; color: #444; }
         #chat {
             height: 250px;
             overflow-y: auto;
             border: 1px solid #ddd;
             padding: 10px;
             margin-bottom: 10px;
             background: #fafafa;
             border-radius: 5px;
         }
         #chat p {
             margin: 5px 0;
             padding: 8px;
             border-radius: 5px;
         }
         .alumno-message { background: #d1ecf1; color: #0c5460; }
         .profesor-message { background: #d4edda; color: #155724; }
         .input-container { display: flex; margin-bottom: 10px; }
         input[type="text"] {
             flex: 1;
             padding: 10px;
             border: 1px solid #ccc;
             border-radius: 4px;
             font-size: 14px;
         }
         button {
             padding: 10px 15px;
             border: none;
             background: #007bff;
             color: #fff;
             border-radius: 4px;
             cursor: pointer;
             margin-left: 5px;
             font-size: 14px;
         }
         button:hover { background: #0069d9; }
         .custom-file-wrapper {
             position: relative;
             display: inline-block;
             width: 70%;
             margin-right: 10px;
         }
         .custom-file-wrapper input[type="file"] {
             position: absolute; top: 0; left: 0;
             width: 100%; height: 100%;
             opacity: 0; cursor: pointer;
         }
         .custom-file-label {
             display: block;
             padding: 10px;
             border: 1px solid #ccc;
             border-radius: 4px;
             background: #fff;
             text-align: center;
             color: #666;
         }
         /* Selector de emojis */
         #emoji-picker {
             text-align: center;
             margin: 10px 0;
         }
         #emoji-picker button {
             background: none;
             border: none;
             cursor: pointer;
             font-size: 20px;
         }
         #emoji-options span {
             cursor: pointer;
             font-size: 20px;
             margin: 0 5px;
         }
      </style>
    </head>
    <body>
      <div class="chat-container">
        <h1>Chat - Profesor</h1>
        <h2>Conectado con Alumno</h2>
        <div id="chat"></div>
        <div class="input-container">
          <input id="mensaje" type="text" placeholder="Escribe un mensaje">
          <button onclick="enviarMensaje()">Enviar</button>
        </div>
        <div id="emoji-picker">
            <button onclick="toggleEmojiPicker()">😀</button>
            <div id="emoji-options" style="display:none;">
                <span onclick="insertEmoji('😀')">😀</span>
                <span onclick="insertEmoji('😂')">😂</span>
                <span onclick="insertEmoji('😍')">😍</span>
                <span onclick="insertEmoji('👍')">👍</span>
                <span onclick="insertEmoji('🙌')">🙌</span>
            </div>
        </div>
        <div class="input-container">
          <div class="custom-file-wrapper">
              <span class="custom-file-label" id="archivo-label">Selecciona un archivo</span>
              <input id="archivo" type="file" onchange="document.getElementById('archivo-label').innerText = this.files[0].name">
          </div>
          <button onclick="enviarArchivo()">Enviar Archivo</button>
        </div>
      </div>
      <script>
         function enviarMensaje(){
             var msg = $("#mensaje").val();
             if(msg.trim() === "") return;
             $.post("/enviar", { mensaje: msg }, function(data){
                 $("#mensaje").val('');
             });
         }
         function enviarArchivo(){
             var fileInput = $("#archivo")[0];
             if(fileInput.files.length == 0) return;
             var file = fileInput.files[0];
             var formData = new FormData();
             formData.append("file", file);
             $.ajax({
                 url: "/upload",
                 type: "POST",
                 data: formData,
                 processData: false,
                 contentType: false,
                 success: function(data){
                     $("#archivo").val('');
                     $("#archivo-label").text("Selecciona un archivo");
                 }
             });
         }
         function actualizarChat(){
             $.get("/mensajes", function(data){
                   $("#chat").html("");
                   data.mensajes.forEach(function(msg){
                         var className = "";
                         if(msg.indexOf("Profesor:") !== -1 || msg.indexOf("Yo (Profesor):") !== -1){
                             className = "profesor-message";
                         } else if(msg.indexOf("Alumno:") !== -1 || msg.indexOf("Yo (Alumno):") !== -1){
                             className = "alumno-message";
                         }
                         $("#chat").append("<p class='" + className + "'>" + msg + "</p>");
                   });
                   $("#chat").scrollTop($("#chat")[0].scrollHeight);
             });
         }
         function toggleEmojiPicker(){
             $("#emoji-options").toggle();
         }
         function insertEmoji(emoji){
             $("#mensaje").val($("#mensaje").val() + emoji);
         }
         $(document).ready(function(){
             $("#mensaje").keypress(function(e) {
                 if(e.which == 13) { enviarMensaje(); }
             });
         });
         setInterval(actualizarChat, 2000);
      </script>
    </body>
    </html>
    ''')

@app.route('/enviar', methods=['POST'])
def enviar():
    msg = request.form.get('mensaje')
    mensajes.append("Yo (Profesor): " + msg)
    # Enviar el mensaje al servidor Alumno
    try:
        r = requests.post(TARGET_ALUMNO_URL + "/recibir", data={'mensaje': msg})
        print("Respuesta de Alumno:", r.text)
    except Exception as e:
        print("Error enviando mensaje a Alumno:", e)
    return jsonify(ok=True)

@app.route('/mensajes')
def get_mensajes():
    return jsonify(mensajes=mensajes)

@app.route('/recibir', methods=['POST'])
def recibir():
    msg = request.form.get('mensaje')
    mensajes.append("Alumno: " + msg)
    return jsonify(ok=True)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        file_link = "<a href='/uploads/{}' target='_blank'>{}</a>".format(filename, filename)
        mensajes.append("Yo (Profesor): Archivo: " + file_link)
        # Reenviar archivo al servidor Alumno
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, file.content_type)}
            try:
                r = requests.post(TARGET_ALUMNO_URL + "/upload?forwarded=true", files=files)
                print("Respuesta upload en Alumno:", r.text)
            except Exception as e:
                print("Error al reenviar archivo:", e)
        return jsonify(ok=True)
    else:
        return jsonify({"error": "File type not allowed"}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5001)))
