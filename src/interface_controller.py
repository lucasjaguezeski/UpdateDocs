import subprocess
import signal
import os
import logging

logging.basicConfig(
    filename=r'logs\errors.log', 
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ReactManager:
    def __init__(self, project_path):
        self.project_path = project_path
        self.process = None

    def start_server(self):
        """Inicia o servidor React"""
        try:
            self.process = subprocess.Popen(
                ["npm", "start"],
                cwd=self.project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
            )
            print("Servidor React iniciado com PID:", self.process.pid)
        except Exception as e:
            logging.error("Erro ao iniciar servidor", exc_info=True)

    def stop_server(self):
        """Para o servidor React"""
        if self.process:
            try:
                # Para Windows
                if os.name == 'nt':
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.process.pid)], check=True)
                # Para Unix/Mac
                else:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                print("Servidor parado com sucesso")
            except Exception as e:
                logging.error("Erro ao parar servidor", exc_info=True)
