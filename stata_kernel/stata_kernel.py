from __future__ import print_function 
import os
import re
import time
import tempfile

import win32com.client
try:
    from ipykernel.kernelbase import Kernel
except ImportError:
    from IPython.kernel.zmq.kernelbase import Kernel
from IPython.core.magic import register_line_cell_magic
from IPython.display import Image
 
from time import strftime
time_name = strftime("%Y_%m_%d_%H_%M_%S")

import base64
import sys
import os

class StataKernel(Kernel):
    implementation = 'StataKernel'
    implementation_version = '0.0.1'
    language = 'Stata Ado and Mata'
    language_version = 'any'
    banner = ''
    language_info = {
        'name': 'stata',
        'mimetype': 'text/x-stata',
        'file_extension': 'do',
    }

    def __init__(self, *args, **kwargs):
        super(StataKernel, self).__init__(*args, **kwargs)
    
        log_address = os.path.join(tempfile.gettempdir(), 'stata_' + time_name + '.txt')
        python_cwd = os.getcwdu() if sys.version_info[0] == 2 else os.getcwd()
        
        self.stata = win32com.client.Dispatch("stata.StataOLEApp")
        self.stata_do = self.stata.DoCommandAsync
        self.stata_do('set linesize 80')
        self.stata_do('log using {} , text replace'.format(log_address))
        self.stata_do('set more off')
        self.stata_do('quietly cd "%s"' % python_cwd + '\n')
        self.stata_do('display "Set the working directory of Stata to: %s"' % python_cwd)
            
        time.sleep(0.5)
        self.log_file = open(log_address)
        self.continuation = False
        
        print('init complete')
        
    def remove_continuations(self, code):
        return re.sub(r'\s*\\\\\\\s*\n', ' ', code)
        
    def get_log_line(self, ntries=10):
        UtilIsStataFree = self.stata.UtilIsStataFree
        log_file = self.log_file
        log_line = log_file.readline()
        try_num = 1
        while not log_line and not UtilIsStataFree():
            time.sleep(0.05)
            log_line = log_file.readline()
            try_num += 1
        return log_line
            
    def ignore_output(self):
        get_log_line = self.get_log_line
        while get_log_line():
            pass
            
    def respond(self, lines=50):
        UtilIsStataFree = self.stata.UtilIsStataFree
        log_file = self.log_file
        log_line = log_file.readline()
        
        while not log_line:
            time.sleep(0.05)
            log_line = log_file.readline()
            
        i = 1    
        while log_line or not UtilIsStataFree():
            if log_line:
            	if i <= lines:
                    stream_content = {'name': 'stdout', 'text': log_line}
                    self.send_response(self.iopub_socket, 'stream', stream_content)
                    i = i + 1
            else:
                time.sleep(0.05)
            log_line = log_file.readline()
            
                 
    def do_execute(
        self,
        code,
        silent,
        store_history=True,
        user_expressions=None,
        allow_stdin=False
    ):
        self.continuation = False
        self.ignore_output()
        code = self.remove_continuations(code.strip())

        graph_magic = re.match(r'\s*%%graph\s+', code)
        
        if graph_magic:

            metadata = {
                'image/png' : {                                             
                    'width': 400,
                    'height': 300
                }
            }
                
            code = code[graph_magic.end():]
            lines = code.split('\n')
          
            i = 1
            for line in lines:
            	    
            	graph_filename = "jupyter_" + time_name + '_' + str(i) + '.png'
                graph_address = os.path.join(tempfile.gettempdir(), graph_filename)   
            	    
                self.stata_do('    ' + line + '\n')
                self.stata_do('quietly graph export "%s", replace width(400) height(300) ' % graph_address + "\n")
                self.stata_do('window manage close graph' + "\n")
                
                self.respond(2)
                
                UtilIsStataFree = self.stata.UtilIsStataFree
  
                while not UtilIsStataFree(): 
                    time.sleep(0.05)         
                                 
            	with open(graph_address, "r+b") as imageFile:
                    base64_bytes = base64.b64encode(imageFile.read())
                    base64_string = base64_bytes.decode('utf-8')
                    dict = {}
                    dict['image/png']= base64_string
                    
                    content = {'data': dict, 'metadata': metadata}
            	    
                self.send_response(self.iopub_socket, 'display_data', content)
                i = i + 1
                
            
        else:
       
            mata_magic = re.match(r'\s*%%mata\s+', code)
            
            if mata_magic:
                code = 'mata\n' + code[mata_magic.end():] + '\nend\n'
        
            delimit = re.match(r'\s*\#delimit\;\s+', code)
            
            if delimit:
            	code = code[delimit.end():] 
            	code = code.replace('#delimit cr','')
                code = ' '.join(code.split())
            	code = code.replace('\n','')
            	code = code.replace(';','\n')
               
            try:
                self.stata_do('    ' + code + '\n')
                self.respond()
                
            except KeyboardInterrupt:
                self.stata.UtilSetStataBreak()
                self.respond()
                return {'status': 'abort', 'execution_count': self.execution_count}
            
        msg = {
            'status': 'ok',
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {}
        }
        return msg
        
    def do_shutdown(self, restart):
        self.stata_do('    exit, clear\n')
                
        
if __name__ == '__main__':
    from IPython.kernel.zmq.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=StataKernel)
