import spidev
import time

spi_bus = int(0)
spi_device = int(0)
spi_max_speed_hz = int(5000000)

def spi_read(address:int,n_bytes:int):
	#to read, force first address bit to 0
	address = address & 0x7F
	result = radio.xfer2([address]+[0x00]*n_bytes)
	return result[1:]

def spi_write(address:int,data:list):
	#to write, force first address bit to 1
	address = address | 0x80
	radio.xfer2([address]+data)

def read_reg(address:int):
	return spi_read(address,1)

radio = spidev.SpiDev()
radio.open(spi_bus,spi_device)
radio.max_speed_hz = spi_max_speed_hz
radio.mode = 0  # SPI mode 0 (polarity=0, phase=0)

print("read reg 0x01")
results = read_reg(0x01)
print(format(results[0],'08b'))
print("read flag register")
print(format(read_reg(0x3E)[0],'08b'))

results[0] &= 0xF8
spi_write(0x01,results)
time.sleep(1)

print("three lsb bits set to 0")
results = read_reg(0x01)
print(format(results[0],'08b'))

#value to be written is frequency/f_step
frequency = 433707000
frequency = int(frequency // (32E6/2**19))
#calculate values to write in each register
data = []
data.append((frequency & 0xFF0000) >> 16)
data.append((frequency & 0xFF00) >> 8)
data.append(frequency & 0xFF)
spi_write(0x06,data)
time.sleep(1)
results = spi_read(0x06,3)
print([format(i,'08b') for i in results])

results = spi_read(0x09,1)
print([format(i,'08b') for i in results])
results[0] |= 0x80
spi_write(0x09, results)
time.sleep(1)
results = spi_read(0x09,1)
print([format(i,'08b') for i in results])

print("whitening")
results = spi_read(0x30,1)
print([format(i,'08b') for i in results])
results[0] &= 0b10011111
results[0] |= 0b01000000
spi_write(0x30, results)
time.sleep(1)
results = spi_read(0x30,1)
print([format(i,'08b') for i in results])

print("mod filter")
results = spi_read(0x0A,1)
print([format(i,'08b') for i in results])
results[0] &= 0b10011111
results[0] |= 0b01100000
spi_write(0x0A, results)
time.sleep(1)
results = spi_read(0x0A,1)
print([format(i,'08b') for i in results])

results[0] |= 0x01
spi_write(0x01,results)
time.sleep(1)
print("first bit set to 1")
print(format(read_reg(0x01)[0],'08b'))

print("read flag register")
print(format(read_reg(0x3E)[0],'08b'))

results = read_reg(0x01)
time.sleep(1)

spi_write(0x26,[200])
time.sleep(1)

print("setting to fstx")
results[0] &= 0xF8
results[0] |= 0x02
spi_write(0x01,results)
print(format(results[0],'08b'))
time.sleep(1)
print("read flag register")
print(format(read_reg(0x3E)[0],'08b'))

print("setting to tx")
results[0] &= 0xF8
results[0] |= 0x03
spi_write(0x01,results)
print(format(results[0],'08b'))
time.sleep(1)
print("read flag register")
print(format(read_reg(0x3E)[0],'08b'))

spi_write(0x00,[0xFF]*64)
while True:
	while( (read_reg(0x3F)[0] & 0b01000000) == 0):
		continue
	spi_write(0x00,[0xFF]*64)
	while( (read_reg(0x3F)[0] & 0b01000000) == 0):
		continue
	results = read_reg(0x01)
	print("setting to fstx")
	results[0] &= 0xF8
	results[0] |= 0x02
	spi_write(0x01,results)
	print(format(results[0],'08b'))
	time.sleep(2)
	
	spi_write(0x00,[0xFF]*64)
	results = read_reg(0x01)
	results[0] &= 0xF8
	results[0] |= 0x03
	spi_write(0x01,results)
	print(format(results[0],'08b'))
	print("read flag register")
	print(format(read_reg(0x3E)[0],'08b'))

radio.close()

# assert False,"hello"