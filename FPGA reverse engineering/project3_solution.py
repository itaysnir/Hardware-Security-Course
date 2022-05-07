from typing import List, Dict, Tuple, Optional
from pprint import pprint
import pathlib
import itertools
import sys, os


HAL_BASE = "/usr/local/"
os.environ["HAL_BASE_PATH"] = HAL_BASE
sys.path.append(HAL_BASE+"lib/")
import hal_py
from hal_py import GateLibraryManager
hal_py.plugin_manager.load_all_plugins()
from hal_plugins import graph_algorithm

graph_algorithms = hal_py.plugin_manager.get_plugin_instance("graph_algorithm")

# This macro should be updated to the verilog file local path
VERILOG_SOURCE_PART_1_PATH = pathlib.Path("/home/hwsec/hal/project2_cipher_v1.v")
VERILOG_SOURCE_PART_2_PATH = pathlib.Path("/home/hwsec/hal/project2_cipher_v2_obfuscated.v")
GATES_LIB_PATH = pathlib.Path("/usr/local/share/hal/gate_libraries/NangateOpenCellLibrary.hgl")
STATES_DIAGRAM_DOT_PATH = pathlib.Path(os.getcwd()) / "states_diagram.dot"


class HWCircuitException(Exception):
    pass


class HwCircuitNoFSMCandidatesException(HWCircuitException):
    pass


class HWCircuit:
    def __init__(
            self,
            verilog_source_path: pathlib.Path,
            gates_lib_path: pathlib.Path,
    ) -> None:
        self.netlist: hal_py.Netlist = hal_py.NetlistFactory.load_netlist(str(verilog_source_path), str(gates_lib_path))
        self.fsm: Optional[List[hal_py.Gate]] = self._get_fsm_candidate()
        self.fsm_gates_module: hal_py.Module = self._get_fsm_gates_module()
        self.combinational_gates_module: hal_py.Module = self._get_combinational_gates()
        self.sequential_gates_module: hal_py.Module = self._get_sequential_gates()
        self.boolean_funcs: List[hal_py.BooleanFunction] = self.get_boolean_funcs()
        self.flipflops_output_nets: List[str] = self._get_flipflops_output_nets()
        self.input_nets: List[str] = self._get_input_nets()
        self.states_diagram: Dict[Tuple[str, str], str] = self.get_states_diagram()

        print('The obtained states diagram:')
        pprint(self.states_diagram)


    def get_gates(self) -> List[hal_py.Gate]:
        return self.netlist.get_gates()

    def _get_fsm_candidate(self) -> Optional[List[hal_py.Gate]]:
        scc_result = graph_algorithms.get_strongly_connected_components(self.netlist)
        fsm_candidates = list(filter(lambda x: len(x) > 1, scc_result))
        fsm_candidates = sorted(fsm_candidates, key=lambda x: len(x))
        try:
            # usually, FSMs are pretty small (however, not 1). Usually it is OK to return the smallest SCC
            return fsm_candidates[0]
        except Exception:
            raise HwCircuitNoFSMCandidatesException()

    def _get_fsm_gates_module(self) -> hal_py.Module:
        return self.netlist.create_module("fsm_gates", self.netlist.get_top_module(), list(self.fsm))

    def _get_combinational_gates(self) -> hal_py.Module:
        combi_gates = []

        for gate in self.fsm:
            if hal_py.GateTypeProperty.combinational in gate.type.get_properties():
                combi_gates.append(gate)

        return self.netlist.create_module("combinational_gates", self.fsm_gates_module, list(combi_gates))

    def _get_sequential_gates(self) -> hal_py.Module:
        seq_gates = []

        for gate in self.fsm:
            if hal_py.GateTypeProperty.sequential in gate.type.get_properties():
                seq_gates.append(gate)

        return self.netlist.create_module("sequential_gates", self.fsm_gates_module, list(seq_gates))

    def _get_flipflops_output_nets(self) -> List[str]:
        output_nets = []
        for gate in self.sequential_gates_module.get_gates():
            Q_output = str(gate.get_fan_out_nets()[0].id)
            Q_not_output = str(gate.get_fan_out_nets()[1].id)
            output_nets.append(Q_output)
            output_nets.append(Q_not_output)

        return output_nets

    def _get_input_nets(self) -> List[str]:
        input_nets = []
        for bool_func in self.boolean_funcs:
            for net_variable in bool_func.get_variables():
                if net_variable in input_nets:
                    continue
                if net_variable not in self.flipflops_output_nets:
                    input_nets.append(net_variable)

        return input_nets

    def get_boolean_funcs(self) -> List[hal_py.BooleanFunction]:
        boolean_funcs = []

        for ff in self.sequential_gates_module.get_gates():
            datapin = ff.get_type().get_pins_of_type(hal_py.PinType.data)

            fanin_net = ff.get_fan_in_net(datapin.pop())
            subgraph_gates = self.dfs_from_net(fanin_net)
            for ff1 in self.sequential_gates_module.get_gates():
                subgraph_gates.remove(ff1)

            tmp_func = hal_py.NetlistUtils.get_subgraph_function(fanin_net, subgraph_gates)
            print(f'Whoo, Got a new boolean func: {str(tmp_func)}')
            boolean_funcs.append(tmp_func)

        return boolean_funcs

    def get_states_diagram(self) -> Dict[Tuple[str, str], str]:
        found_states = {}
        states_length = len(self.sequential_gates_module.get_gates())
        possible_states = list(itertools.product(["0", "1"], repeat=states_length))
        possible_inputs = list(itertools.product(["0", "1"], repeat=len(self.input_nets)))

        for state in possible_states:
            instate = {}
            for i, state_bit in enumerate(state):
                if state_bit == "0":
                    # Each flip flop contains TWO output nets - Q, Qn!
                    instate[self.flipflops_output_nets[2 * i]] = hal_py.BooleanFunction.Value.ZERO
                    instate[self.flipflops_output_nets[(2 * i) + 1]] = hal_py.BooleanFunction.Value.ONE
                else:
                    instate[self.flipflops_output_nets[2 * i]] = hal_py.BooleanFunction.Value.ONE
                    instate[self.flipflops_output_nets[(2 * i) + 1]] = hal_py.BooleanFunction.Value.ZERO

            for input in possible_inputs:
                for i, input_bit in enumerate(input):
                    if input_bit == "0":
                        instate[self.input_nets[i]] = hal_py.BooleanFunction.Value.ZERO
                    else:
                        instate[self.input_nets[i]] = hal_py.BooleanFunction.Value.ONE

                new_state_result = ''
                for bool_func in self.boolean_funcs:
                    new_state_result += self.get_state_str([bool_func.evaluate(instate)])

                found_states[(''.join(state), ''.join(input))] = new_state_result

        return found_states

    def print_graph(self) -> None:
        content = "digraph StatesFSM {\n"

        printed_states = []

        for inputs, result_state in self.states_diagram.items():
            current_state = inputs[0]
            current_input = inputs[1]
            if (current_state, result_state) not in printed_states:
                content += f"\t{current_state} -> {result_state} ;\n"
                # uncomment this if printing with inputs is desired
                #content += f"\t{current_state} -> {result_state} [label={current_input}];\n"
                printed_states.append((current_state, result_state))

        content += "}"

        with open (STATES_DIAGRAM_DOT_PATH, 'w') as f:
            f.write(content)

    @staticmethod
    def dfs_from_net(net: hal_py.Net) -> List[hal_py.Gate]:
        gate_list = []
        stack = [net]
        while (stack):
            n = stack.pop()
            for endpoint in n.get_sources():
                gate = endpoint.get_gate()
                if gate not in gate_list:
                    gate_list.append(gate)
                    for net in gate.get_fan_in_nets():
                        if not net.is_global_input_net():
                            stack.append(net)

        return gate_list

    @staticmethod
    def get_state_str(state_dict) -> str:
        return_str = ""

        for id in state_dict:
            if id == hal_py.BooleanFunction.Value.ZERO:
                return_str += '0'
            else:
                return_str += '1'

        return return_str


def main():
    circuit = HWCircuit(VERILOG_SOURCE_PART_2_PATH, GATES_LIB_PATH)
    circuit.print_graph()


if __name__ == '__main__':
    main()
