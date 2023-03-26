import numpy as np
import argparse


class DataFile:
    def __init__(self, data, window_size):
        self.current_byte = None
        self.data = data
        self.window_size = window_size
        self.window = [0] * self.window_size
        self.output = []
        self.byte_offset = 0
        self.bit_offset = 8
        self.file_mask = 0x80

    def get_bits(self, num_bits):
        result = np.uint32(0)
        while num_bits > 0:
            result = result << 1
            if (self.file_mask & self.data[self.byte_offset]) > 0:
                result |= 1
            self.file_mask = self.file_mask >> 1
            if self.file_mask == 0:
                self.file_mask = 0x80
                self.byte_offset += 1
            num_bits -= 1
        return result

    def write_byte(self, byte):
        self.output.append(byte)

    def mod_window(self, i):
        return i & self.window_size - 1


def decompress(input_data, b, l):
    # print(f"Input Data length: {len(input_data)}")
    window_size = 1 << b
    # print(f"Window Size: {window_size}")
    data_file = DataFile(input_data, window_size)
    index_b_count = b
    length_b_count = l
    num = 1
    while True:
        if data_file.get_bits(1) > 0:
            num2 = data_file.get_bits(8)
            data_file.write_byte(num2)
            data_file.window[num] = num2
            num = data_file.mod_window(num + 1)
        else:
            bits = data_file.get_bits(index_b_count)
            if bits == 0:
                break
            num3 = data_file.get_bits(length_b_count)
            num3 = num3 + int((1 + index_b_count + length_b_count) / 9)
            for i in range(num3 + 1):
                num2 = data_file.window[data_file.mod_window(num - bits)]
                data_file.write_byte(num2)
                data_file.window[num] = num2
                num = data_file.mod_window(num + 1)
    return data_file.output


def getByteAndLength(input_data):
    index_b_count = (input_data & 0xF0) >> 4
    length_b_count = (input_data & 0x07)
    return index_b_count, length_b_count


def print_hex(input_data):
    # Print output as hex
    hex_output = ''.join(f'{b:02x}' for b in input_data)
    print(f"Hex output({int(len(hex_output) / 2)}): {hex_output}")
    return


def print_ascii(input_data):
    # Print output as ASCII
    ascii_output = ''.join(chr(b) if 32 <= b < 127 else '.' for b in input_data)
    print(f"ASCII output: {ascii_output}")
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='GridStream_Decompressor.py',
                                     description='LZSS GridStream decompression tool using the first byte of an array '
                                                 'as byte/length to process the rest of the array. '
                                                 'Also includes brute-force functionality to test all possible values.',
                                     epilog='HACK THE PLANET!')
    parser.add_argument('hex_string', type=str, help='This is the string of data you want to decompress in hex. '
                                                     'Ex. AA23E57F2E4B  but much longer than this...')
    parser.add_argument('--index', type=int, help="Manually supply index, don't use first byte of array for this")
    parser.add_argument('--length', type=int, help="Manually supply length, don't use first byte of array for this")
    parser.add_argument('--brute_force', action='store_true', help="Try all possible values for index/length and print "
                                                                   "results")
    args = parser.parse_args()

    data = bytearray.fromhex(args.hex_string)

    if args.index and args.length:
        # Path where user supplies index/length for us
        index = args.index
        length = args.length
        print(f"Index: {index}, Length: {length}")
        output = decompress(data, index, length)
        print_hex(output)
        print_ascii(output)
    elif not args.index and not args.length and not args.brute_force:
        # Path where the user supplies a string and we extract index/length
        index, length = getByteAndLength(data[0])
        print(f"Index: {index}, Length: {length}")
        del data[0]
        output = decompress(data, index, length)
        print_hex(output)
        print_ascii(output)
    elif args.brute_force:
        # path where user specifies brute force attack
        for index in range(16):
            for length in range(8):
                # print(byte, length)
                output = [0]
                try:
                    output = decompress(data, index, length)
                except IndexError:
                    print(f"Skipping invalid attempt, Index: {index}, Length: {length}")
                    break
                if len(output) > len(data):
                    print(f"Index: {index}, Length: {length}")
                    print_hex(output)
                    print_ascii(output)
                else:
                    print(
                        f"Uncompressed output ({len(output)}) shorter than compressed input ({len(data)}), discarding.")
