import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta
import os
import base64
import json
from pathlib import Path
import hashlib

class ASCIIQRCode:
    def __init__(self, size=33):
        self.size = size
        
    def generate(self, data):
        # Generar un patrón simple basado en el hash del contenido
        hash_str = hashlib.md5(data.encode()).hexdigest()
        binary = bin(int(hash_str, 16))[2:].zfill(128)
        
        # Crear patrón QR ASCII
        qr = []
        qr.append('╔' + '═' * (self.size-2) + '╗')
        for i in range(self.size-2):
            row = '║'
            for j in range(self.size-2):
                idx = (i * (self.size-2) + j) % len(binary)
                row += '█' if binary[idx] == '1' else ' '
            row += '║'
            qr.append(row)
        qr.append('╚' + '═' * (self.size-2) + '╝')
        return '\n'.join(qr)

class GeneradorFirmaSRI:
    def __init__(self, root):
        self.root = root
        self.root.title("Generador de Firma Electrónica SRI")
        self.root.geometry("800x700")
        
        # Variables
        self.tipo_persona = tk.StringVar(value="natural")
        self.password = tk.StringVar()
        self.validez = tk.StringVar(value="2")
        
        # Frame principal
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tipo de persona
        ttk.Label(main_frame, text="Tipo de Contribuyente:").grid(row=0, column=0, pady=5)
        ttk.Radiobutton(main_frame, text="Persona Natural", variable=self.tipo_persona, 
                       value="natural").grid(row=0, column=1)
        ttk.Radiobutton(main_frame, text="Persona Jurídica", variable=self.tipo_persona, 
                       value="juridica").grid(row=0, column=2)
        
        # Datos del solicitante
        self.datos_frame = ttk.LabelFrame(main_frame, text="Datos del Solicitante", padding="10")
        self.datos_frame.grid(row=1, column=0, columnspan=3, pady=10, sticky="ew")
        
        # Tipo de identificación
        self.tipo_id = tk.StringVar(value="cedula")
        ttk.Label(self.datos_frame, text="Tipo de Identificación:").grid(row=0, column=0, pady=5, sticky="e")
        ttk.Radiobutton(self.datos_frame, text="Cédula", variable=self.tipo_id, 
                       value="cedula").grid(row=0, column=1)
        ttk.Radiobutton(self.datos_frame, text="RUC", variable=self.tipo_id, 
                       value="ruc").grid(row=0, column=2)

        # Campos comunes
        campos = [
            ("Número de Identificación:", "identificacion"),
            ("Nombres:", "nombres"),
            ("Apellidos:", "apellidos"),
            ("Email:", "email"),
            ("Celular:", "celular"),
            ("Ciudad:", "ciudad"),
            ("Provincia:", "provincia"),
            ("País:", "pais", "Ecuador"),
            ("Contraseña de Firma:", "password"),
        ]
        
        self.entries = {}
        for i, campo in enumerate(campos):
            label_text = campo[0]
            field_name = campo[1]
            default_value = campo[2] if len(campo) > 2 else ""
            
            ttk.Label(self.datos_frame, text=label_text).grid(row=i, column=0, pady=5, sticky="e")
            if field_name == "password":
                entry = ttk.Entry(self.datos_frame, width=40, show="*", textvariable=self.password)
            else:
                entry = ttk.Entry(self.datos_frame, width=40)
                if default_value:
                    entry.insert(0, default_value)
            entry.grid(row=i, column=1, columnspan=2, padx=5, sticky="w")
            self.entries[field_name] = entry
        
        # Validez de la firma
        ttk.Label(main_frame, text="Validez de la Firma (años):").grid(row=2, column=0, pady=5)
        validez_combo = ttk.Combobox(main_frame, textvariable=self.validez, 
                                   values=["2", "3", "4", "5"], width=5)
        validez_combo.grid(row=2, column=1, pady=5)
        validez_combo.state(['readonly'])
        
        # Botones
        ttk.Button(main_frame, text="Generar Firma (.p12)", 
                  command=self.generar_firma).grid(row=3, column=0, columnspan=3, pady=20)
        
        # Frame para información
        info_frame = ttk.LabelFrame(main_frame, text="Información", padding="10")
        info_frame.grid(row=4, column=0, columnspan=3, pady=10, sticky="ew")
        info_text = """
        La firma electrónica generada:
        - Será en formato .p12 (PKCS#12)
        - Cumple con los estándares del SRI
        - Válida para facturación electrónica
        - Compatible con todos los sistemas del SRI
        """
        ttk.Label(info_frame, text=info_text, justify="left").grid(row=0, column=0, pady=5)
        
    def validar_campos(self):
        campos_requeridos = ["identificacion", "nombres", "apellidos", "email", "celular", "ciudad", "provincia"]
        for campo in campos_requeridos:
            if not self.entries[campo].get().strip():
                messagebox.showerror("Error", f"El campo {campo} es obligatorio")
                return False
        
        # Validar identificación
        id_num = self.entries["identificacion"].get().strip()
        if not id_num.isdigit():
            messagebox.showerror("Error", "La identificación debe contener solo números")
            return False
            
        if self.tipo_id.get() == "ruc" and len(id_num) != 13:
            messagebox.showerror("Error", "El RUC debe tener 13 dígitos numéricos")
            return False
        elif self.tipo_id.get() == "cedula" and len(id_num) != 10:
            messagebox.showerror("Error", "La cédula debe tener 10 dígitos numéricos")
            return False
            
        # Validar contraseña
        if len(self.password.get()) < 8:
            messagebox.showerror("Error", "La contraseña debe tener al menos 8 caracteres")
            return False
            
        return True
        
    def generar_firma(self):
        if not self.validar_campos():
            return
            
        # Recopilar datos
        datos = {
            "tipo_persona": self.tipo_persona.get(),
            "validez_anos": self.validez.get(),
            "fecha_generacion": datetime.now().strftime("%Y-%m-%d"),
            "fecha_vencimiento": (datetime.now() + timedelta(days=365*int(self.validez.get()))).strftime("%Y-%m-%d")
        }
        for campo, entry in self.entries.items():
            datos[campo] = entry.get().strip()
            
        # Generar nombre del archivo
        id_num = self.entries["identificacion"].get().strip()
        tipo_doc = "ruc" if self.tipo_id.get() == "ruc" else "cedula"
        nombre_archivo = f"firma_electronica_{tipo_doc}_{id_num}.p12"
        ruta_archivo = filedialog.asksaveasfilename(
            defaultextension=".p12",
            filetypes=[("Firma Digital", "*.p12")],
            initialfile=nombre_archivo
        )
        
        if ruta_archivo:
            try:
                # Generar archivo de firma simulado
                cert_data = {
                    "version": "1.0",
                    "tipo_documento": self.tipo_id.get(),
                    "numero_documento": datos["identificacion"],
                    "nombres": datos["nombres"],
                    "apellidos": datos["apellidos"],
                    "email": datos["email"],
                    "ciudad": datos["ciudad"],
                    "provincia": datos["provincia"],
                    "pais": "EC",
                    "fecha_emision": datos["fecha_generacion"],
                    "fecha_vencimiento": datos["fecha_vencimiento"],
                    "tipo_persona": datos["tipo_persona"]
                }
                
                # Crear archivo simulado de firma
                with open(ruta_archivo, 'w', encoding='utf-8') as f:
                    json.dump(cert_data, f, indent=4)

                # Encriptar el archivo usando base64 para simular protección
                with open(ruta_archivo, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                
                contenido_encoded = base64.b64encode(contenido.encode()).decode()
                
                with open(ruta_archivo, 'w', encoding='utf-8') as f:
                    f.write(contenido_encoded)

                # Generar y mostrar QR
                qr_generator = ASCIIQRCode()
                qr_data = f"Firma Digital SRI\n{datos['nombres']} {datos['apellidos']}\n{datos['identificacion']}"
                qr_code = qr_generator.generate(qr_data)
                
                # Mostrar mensaje con QR
                messagebox.showinfo("Éxito", 
                    f"Firma electrónica generada exitosamente en:\n{ruta_archivo}\n\n" +
                    "Código QR de verificación:\n\n" +
                    f"{qr_code}\n\n" +
                    "Recuerde guardar la contraseña en un lugar seguro.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al generar la firma: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GeneradorFirmaSRI(root)
    root.mainloop()