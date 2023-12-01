
from abc import ABCMeta, abstractmethod

class DragonflyHardwareResponse():
    def __init__(self,
                success:bool,
                description:str,
                payload:dict):
        self.success = success 
        self.description = description 
        self.payload=payload 
        self.hardware_type = None 


class DCPHardware(metaclass=ABCMeta):
    
    @abstractmethod 
    def get_status(self):
        pass 
    @property
    @abstractmethod
    def state(self):
        pass 
    @abstractmethod 
    def connect(self):
        pass 
    @abstractmethod 
    def disconnect(self):
        pass 
    @abstractmethod 
    def start_polling(self):
        pass 
    @abstractmethod 
    def stop_polling(self):
        pass 
    @abstractmethod 
    def set_polling_interval(self):
        pass 
    
    @property
    @abstractmethod
    def is_connected(self):
        pass 