import logging
import random
import time
from math import log, ceil


logger = logging.getLogger(__name__)


class ModularExpException(Exception):
    pass


class ModularExp(object):
    hamming_weight_time_dependency = []

    def __init__(self, c):
        super(ModularExp, self).__init__()
        self.bit_count = c
        self.a = 0
        self.e = 0
        self.n = 0
        self.weights_trace = []

    @property
    def exp_hamming_weight(self):
        return bin(self.e).count('1')

    @property
    def k_array(self):
        return list(bin(self.e)[len('0b'):])[::-1]

    @staticmethod
    def _square_operation(a, modulus):
        return ((a * a) % modulus)

    @staticmethod
    def _multiply_operation(a, b, modulus):
        return ((a * b) % modulus)

    @staticmethod
    def _faulty_operation(a, b):
        return ((a ^ b) ^ 0x1337)

    @staticmethod
    def _generate_random_triplet(bit_count):
        a = random.getrandbits(bit_count)
        b = random.getrandbits(bit_count)
        c = 0
        while c % 2 == 0:
            c = random.getrandbits(bit_count)                   # n must be odd for montgomery

        return a, b, c

    @staticmethod
    def _calculate_R(modulus):
        r = pow(2, ceil(log(modulus) / log(2)))
        r_inverse = pow(r, -1, modulus)

        return r, r_inverse

    def generate_random_numbers(self):
        print('Generating random parameters (a, e, n)..')

        self.a, self.e, self.n = ModularExp._generate_random_triplet(self.bit_count)
        self.r, self.r_inverse = ModularExp._calculate_R(self.n)

        print(f'Generated Random Parameters:\n'
              f'A: {self.a}\n'
              f'EXP: {self.e}\n'
              f'EXP BITS: {bin(self.e)}\n'
              f'MODULUS(N): {self.n}\n'
              f'R: {self.r}\n'
              f'R_INVERSE: {self.r_inverse}\n')

    def basic_exponentiation(self, base, k_array, modulus):
        b = base ** int(k_array[0])
        c = base
        for i in range(1, len(k_array)):
            c = ModularExp._square_operation(c, modulus)
            self.weights_trace.append(50)  # holds for square weight
            if k_array[i] == '1':
                b = ModularExp._multiply_operation(b, c, modulus)
                self.weights_trace.append(100)  # holds for multiply weight

        return b

    def dummy_multiply_exponentiation(self, base, k_array, modulus):
        b = [0, 0]
        b[0] = base ** int(k_array[0])

        c = base
        for i in range(1, len(k_array)):
            c = ModularExp._square_operation(c, modulus)
            self.weights_trace.append(50)
            b[(1 - int(k_array[i]))] = ModularExp._multiply_operation(b[0], c, modulus)
            self.weights_trace.append(100)

        return b[0]

    def faulty_dummy_multiply_exponentiation(self, k_array, base, modulus, faulty_iteration):
        b = [0, 0]
        b[0] = base ** int(k_array[0])
        c = base
        for i in range(1, len(k_array)):
            c = ModularExp._square_operation(c, modulus)
            self.weights_trace.append(50)
            if i != faulty_iteration:
                b[(1 - int(k_array[i]))] = ModularExp._multiply_operation(b[0], c, modulus)
            else:
                b[(1 - int(k_array[i]))] = ModularExp._faulty_operation(b[0], c)
            self.weights_trace.append(100)

        return b[0]

    def montgomery_multiply(self, a, b):
        a_tag = ((a * self.r) % self.n)
        b_tag = ((b * self.r) % self.n)
        c_tag = (((a_tag * b_tag) * self.r_inverse) % self.n)
        c = ((c_tag * self.r_inverse) % self.n)

        return c

    def montgomery_exponentiation(self, k_array, base):
        R_0 = 1
        R_1 = base

        for j in range(len(k_array))[::-1]:
            if k_array[j] == '0':
                R_1 = self.montgomery_multiply(R_0, R_1)
                self.weights_trace.append(100)              # multiply weight
                R_0 = self.montgomery_multiply(R_0, R_0)
                self.weights_trace.append(50)               # square weight
            else:  # k_array[j] == '1'
                R_0 = self.montgomery_multiply(R_0, R_1)
                self.weights_trace.append(100)
                R_1 = self.montgomery_multiply(R_1, R_1)
                self.weights_trace.append(50)

        return R_0

    def faulty_montgomery_exponentiation(self, k_array, base, faulty_iteration):
        R_0 = 1
        R_1 = base

        for j in range(len(k_array))[::-1]:
            if j != faulty_iteration:
                if k_array[j] == '0':
                    R_1 = self.montgomery_multiply(R_0, R_1)
                    R_0 = self.montgomery_multiply(R_0, R_0)
                else:  # k_array[j] == '1'
                    R_0 = self.montgomery_multiply(R_0, R_1)
                    R_1 = self.montgomery_multiply(R_1, R_1)
            else:
                if k_array[j] == '0':
                    R_1 = self._faulty_operation(R_0, R_1)
                    R_0 = self.montgomery_multiply(R_0, R_0)
                else:  # k_array[j] == '1'
                    R_0 = self._faulty_operation(R_0, R_1)
                    R_1 = self.montgomery_multiply(R_1, R_1)

        return R_0

    def run_project(self):
        try:
            print('Basic Right-to-left Exponentiation Starts..')
            del self.weights_trace[:]
            start_time = time.time()
            basic_exp_result = self.basic_exponentiation(self.a, self.k_array, self.n)
            end_time = time.time()
            time_diff = end_time - start_time
            # self.hamming_weight_time_dependency.append((self.exp_hamming_weight, time_diff))
            print(
                f'Calculation Success!\n'
                f'RESULT: {basic_exp_result}\n'
                f'EXECUTION TIME: {time_diff}[seconds]\n'
                f'Weights Trace: {self.weights_trace}\n'
            )
        except Exception:
            ModularExpException('Basic Calculation failed..')


        try:
            print('Basic Dummy Multiply Exponentiation Starts..')
            del self.weights_trace[:]
            start_time = time.time()
            dummy_exp_result = self.dummy_multiply_exponentiation(self.a, self.k_array, self.n)
            end_time = time.time()
            time_diff = end_time - start_time
            print(
                f'Dummy Multiplication Calculation Success!\n'
                f'RESULT: {dummy_exp_result}\n'
                f'EXECUTION TIME: {time_diff}[seconds]\n'
                f'Weights Trace: {self.weights_trace}\n'
            )
        except Exception:
            ModularExpException('Dummy Basic Calculation failed..')


        try:
            print('Montgomery Exponentiation Starts..')
            del self.weights_trace[:]
            start_time = time.time()
            montgomery_result = self.montgomery_exponentiation(self.k_array, self.a)
            end_time = time.time()
            time_diff = end_time - start_time
            print(
                f'Montgomery Calculation Success!\n'
                f'RESULT: {montgomery_result}\n'
                f'EXECUTION TIME: {time_diff}[seconds]\n'
            )
        except Exception:
            ModularExpException('Montgomery calculation failed..')


        try:
            print('C-Error Attack For Dummy Multiplication Basic Exponentiation Starts '
                  '(might be long operation)..')
            del self.weights_trace[:]
            restored_key = self.c_safe_error_attack()
            assert(restored_key == self.k_array)                    # SUCCESS!
            print(f'Successfully broke the secret key, Result (LSB at index 0):\n'
                  f'{restored_key}\n'
                  f'Or as an Integer:\n'
                  f'{self.e}')
        except Exception:
            ModularExpException('C-safe error attack on dummy multiplication basic exponentiation failed..')


        try:
            print('C-Error Attack For Dummy Multiplication Montgomery Exponentiation Starts '
                  '(might be long operation)..')
            del self.weights_trace[:]
            restored_key = self.c_safe_error_attack_montgomery_failure()
            assert(restored_key != self.k_array)                    # FAILURE!!
            print(f'Couldnt break the secret key with C-ERROR-ATTACK!\n'
                  f'Montgomery ladder algorithm is being used..')

        except Exception:
            ModularExpException('C-safe error attack on dummy multiplication basic exponentiation failed..')

    def c_safe_error_attack(self):
        original_output = self.dummy_multiply_exponentiation(self.a, self.k_array, self.n)
        restored_key = ''
        for i in range(self.bit_count):   # The multiplication algorithm skips iteration 0, assumes LSB == '0' for now
            if original_output != self.faulty_dummy_multiply_exponentiation(self.k_array,
                                                                   self.a,
                                                                   self.n,
                                                                   faulty_iteration=i):
                restored_key = '1' + restored_key
            else:
                restored_key = '0' + restored_key

        restored_key = list(restored_key)[::-1]
        # Now check if LSB is OK-
        # The encryption algorithm does not iterate over k[0], we have to validate this manually.
        if original_output != self.dummy_multiply_exponentiation(self.a, restored_key, self.n):
            restored_key[0] = '1'                           # Because default is assumed to be 0
        restored_key = restored_key[:len(self.k_array)]     # Fix padding

        return restored_key

    def c_safe_error_attack_montgomery_failure(self):
        original_output = self.montgomery_exponentiation(self.k_array, self.a)
        restored_key = ''
        for i in range(self.bit_count):  # The multiplication algorithm skips iteration 0, assumes LSB == '0' for now
            if original_output != self.faulty_montgomery_exponentiation(self.k_array, self.a, faulty_iteration=i):
                restored_key = '1' + restored_key
            else:
                restored_key = '0' + restored_key

        restored_key = list(restored_key)[::-1]
        # Now check if LSB is OK-
        # The encryption algorithm does not iterate over k[0], we have to validate this manually.
        if original_output != self.montgomery_exponentiation(restored_key, self.a):
            restored_key[0] = '1'  # Because default is assumed to be 0
        restored_key = restored_key[:len(self.k_array)]  # Fix padding

        return restored_key