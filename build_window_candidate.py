import hashlib, pathlib, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

root = pathlib.Path(__file__).parent
data=bytearray((root/'codex-computer-use-0.7.18.candidate.exe').read_bytes())
assert hashlib.sha256(data).hexdigest()=='7bcf0b19481a96f478760a345b389ae47c44d6e2a6f745b331b9043cd9f7e804'
pe=pefile.PE(data=bytes(data))
def change(rva, old, new):
    off=pe.get_offset_from_rva(rva); old=bytes.fromhex(old); new=bytes.fromhex(new)
    assert len(old)==len(new) and data[off:off+len(old)]==old, hex(rva)
    data[off:off+len(new)]=new
# Reuse unused padding in the existing private executable section.
stub_rva=0x17c0d0
stub=bytearray.fromhex('488b8424d0010000488944244031ff4531e4e9')
stub += struct.pack('<i',0x3d9f5-(stub_rva+len(stub)+4))
off=pe.get_offset_from_rva(stub_rva)
assert data[off:off+len(stub)]==bytes(len(stub))
data[off:off+len(stub)]=stub
struct.pack_into('<I',data,0x2f0+8,0x100)
jump=b'\xe9'+struct.pack('<i',stub_rva-(0x3d9ec+5))+b'\x90'*4
change(0x3d9ec,'2b7c2464442b642468',jump.hex())
# IGraphicsCaptureItemInterop vtable: slot 3 CreateForWindow replaces slot 4 CreateForMonitor.
change(0x3de1e,'ff5020','ff5018')
out=root/'codex-computer-use-0.7.18.window-candidate.exe'; out.write_bytes(data)
md=Cs(CS_ARCH_X86,CS_MODE_64)
for ins in md.disasm(bytes(stub),stub_rva): print(hex(ins.address),ins.mnemonic,ins.op_str)
print('SHA256',hashlib.sha256(data).hexdigest())
