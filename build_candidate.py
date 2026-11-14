import hashlib, pathlib, re, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

root = pathlib.Path(__file__).parent
data = bytearray((root / 'codex-computer-use-0.7.18.original.exe').read_bytes())
assert hashlib.sha256(data).hexdigest() == 'f8ad259caa82bc2a62c26cb1a3428e558d26959de7b4d5bce0d708f5c40e81d9'
pe = pefile.PE(data=bytes(data))
source = (root / 'community-patcher.ps1').read_text(encoding='utf-8-sig')
profile = source.split("Name = '@oai/sky 0.7.17 helper 7F73CF56")[1].split('function Write-Log')[0]
regions = {m.group(1): (int(m.group(2),16), bytes.fromhex(m.group(3)), bytes.fromhex(m.group(4))) for m in re.finditer(r"(?s)Name = '([^']+)'\s+Offset = (0x[0-9a-f]+)\s+OriginalHex = '([0-9a-f]+)'\s+PatchedHex = '([0-9a-f]+)'",profile)}
def change(off, original, new):
    assert data[off:off+len(original)] == original, hex(off)
    assert len(original)==len(new)
    data[off:off+len(new)] = new
def region(name):
    off, before, after = regions[name]; change(off,before,after)
for name in ('pe-section-count','pe-size-of-code','pe-size-of-image','pe-certificate-directory','mta-section-header'):
    region(name)
change(0xd8, bytes(data[0xd8:0xdc]), bytes(4))
def at_rva(rva, before, after): change(pe.get_offset_from_rva(rva),bytes.fromhex(before),bytes.fromhex(after))
at_rva(0x42579, '0f855b310000', '0f853d310000')
at_rva(0x4258a, '740d', 'eb0d')
at_rva(0x12cf00, '4425044001000000', '00c0174001000000')
change(0x124, struct.pack('<I',0x8478), struct.pack('<I',0x8490))
change(0x208, struct.pack('<I',0x8478), struct.pack('<I',0x8490))
change(pe.get_offset_from_rva(0x158478), bytes(24), bytes.fromhex('00c0170072c01700c0c0170080c01700b2c01700c8c01700'))
wrapper = bytearray(regions['mta-wrapper-and-unwind'][2])
# Rebind only the four known IAT calls and the original callback call, preserving instruction sizes.
iat = {x.name.decode():x.address-pe.OPTIONAL_HEADER.ImageBase for e in pe.DIRECTORY_ENTRY_IMPORT for x in e.imports if x.name}
md=Cs(CS_ARCH_X86,CS_MODE_64)
for start, size, targets in [(0,0x72,['CreateThread','CloseHandle']), (0x80,0x32,['RoInitialize',None,'RoUninitialize'])]:
    calls=[ins for ins in md.disasm(bytes(wrapper[start:start+size]),0x17c000+start) if ins.mnemonic=='call' and (ins.bytes[0]==0xe8 or ins.bytes[:2]==b'\xff\x15')]
    assert len(calls)==len(targets), [(hex(i.address),i.op_str) for i in calls]
    for ins,name in zip(calls,targets):
        target=0x42544 if name is None else iat[name]
        offset=ins.address-0x17c000
        assert ins.bytes[0] in (0xe8,0xff)
        displacement=target-(ins.address+ins.size)
        struct.pack_into('<i',wrapper,offset+ins.size-4,displacement)
off=0x176400
data[off:off+len(wrapper)]=wrapper
candidate=root/'codex-computer-use-0.7.18.candidate.exe'
candidate.write_bytes(data)
print('Candidate SHA-256:',hashlib.sha256(data).hexdigest())
print('Candidate:',candidate)
