import modular_exp
import time
import matplotlib.pyplot as plt


def measure_time_execution_to_bit_count_dependency():
    x_values = range(1, 3000)
    y_values = []
    for bit_count in x_values:
        mod = modular_exp.ModularExp(c=bit_count)
        mod.generate_random_numbers()
        start_time = time.time()
        basic_exp_result = mod.basic_exponentiation(mod.a, mod.k_array, mod.n)
        end_time = time.time()
        time_diff = end_time - start_time
        y_values.append(time_diff)

    plt.plot(x_values, y_values)
    plt.xlabel('Bit Count')
    plt.ylabel('Execution Time [seconds]')
    plt.title('Basic Right To Left Exponentiation')

    plt.show()

def measure_time_execution_to_hamming_weight_dependency():
    x_values = []
    y_values = []
    mod = modular_exp.ModularExp(c=2000)
    for iteration_no in range(200):
        mod.generate_random_numbers()
        hamming_weight = mod.exp_hamming_weight
        if hamming_weight in x_values:
            continue
        x_values.append(hamming_weight)
        start_time = time.time()
        basic_exp_result = mod.basic_exponentiation(mod.a, mod.k_array, mod.n)
        end_time = time.time()
        time_diff = end_time - start_time
        y_values.append(time_diff)
        print(f'Time to hamming weight: {hamming_weight} , {time_diff}')

    plt.scatter(x_values, y_values)
    plt.xlabel('Hamming Weight')
    plt.ylabel('Execution Time [seconds]')
    plt.title('Basic right to left exponentiation')

    plt.show()

def measure_trace():
    mod = modular_exp.ModularExp(c=50)
    mod.generate_random_numbers()
    basic_exp_result = mod.basic_exponentiation(mod.a, mod.k_array, mod.n)
    print(f'Resulting Trace:\n'
          f'{mod.weights_trace}')

def measure_time_execution_to_hamming_weight_dependency_dummy_operation():
    x_values = []
    y_values = []
    mod = modular_exp.ModularExp(c=2000)
    for iteration_no in range(200):
        mod.generate_random_numbers()
        hamming_weight = mod.exp_hamming_weight
        if hamming_weight in x_values:
            continue
        x_values.append(hamming_weight)
        start_time = time.time()
        print(mod.k_array)
        mod.dummy_multiply_exponentiation(mod.a, mod.k_array, mod.n)
        end_time = time.time()
        time_diff = end_time - start_time
        y_values.append(time_diff)
        print(f'Time to hamming weight: {hamming_weight} , {time_diff}')

    plt.scatter(x_values, y_values)
    plt.xlabel('Hamming Weight')
    plt.ylabel('Execution Time [seconds]')
    plt.title('Dummy Operation Exponentiation')

    plt.show()

def measure_dummy_operation_trace():
    mod = modular_exp.ModularExp(c=50)
    mod.generate_random_numbers()
    basic_exp_result = mod.dummy_multiply_exponentiation(mod.a, mod.k_array, mod.n)
    print(f'Resulting Trace:\n'
          f'{mod.weights_trace}')

def measure_time_execution_to_hamming_weight_dependency_montgomery_operation():
    x_values = []
    y_values = []
    mod = modular_exp.ModularExp(c=2000)
    for iteration_no in range(200):
        mod.generate_random_numbers()
        hamming_weight = mod.exp_hamming_weight
        if hamming_weight in x_values:
            continue
        x_values.append(hamming_weight)
        start_time = time.time()
        basic_exp_result = mod.montgomery_exponentiation(mod.k_array, mod.a)
        end_time = time.time()
        time_diff = end_time - start_time
        y_values.append(time_diff)
        print(f'Time to hamming weight: {hamming_weight} , {time_diff}')

    plt.scatter(x_values, y_values)
    plt.xlabel('Hamming Weight')
    plt.ylabel('Execution Time [seconds]')
    plt.title('Montgomery Exponentiation')

    plt.show()

def measure_montgomery_operation_trace():
    mod = modular_exp.ModularExp(c=50)
    mod.generate_random_numbers()
    basic_exp_result = mod.montgomery_exponentiation(mod.k_array, mod.a)
    print(f'Resulting Trace:\n'
          f'{mod.weights_trace}')

def main():
    print(f'Hello, Welcome to Itay & Eviatar project.\n'
          f'This is a simulator for hardware-security Project 1'
          f'We will simulate multiple variants of modular exponentiation techniques.\n')
    # measure_time_execution_to_bit_count_dependency()
    # measure_time_execution_to_hamming_weight_dependency()
    # measure_trace()
    # measure_time_execution_to_hamming_weight_dependency_dummy_operation()
    # measure_dummy_operation_trace()
    # measure_time_execution_to_hamming_weight_dependency_montgomery_operation()
    # measure_montgomery_operation_trace()

    mod = modular_exp.ModularExp(c=2000)
    mod.generate_random_numbers()
    mod.run_project()


if __name__ == '__main__':
    main()
