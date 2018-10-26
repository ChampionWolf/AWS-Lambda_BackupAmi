from CreateAmi import createAmi
from DeregisterOldAMIs import deregisterOldAmis

# Running Script
def run(event, context):
    createAmi()
    deregisterOldAmis()

