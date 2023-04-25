import json
from pathlib import Path
import argparse

rels = [
#  'Analytics_NonModeledMSTORE',
#  'Analytics_NonModeledMLOAD',
#  'Analytics_PublicFunctionArg',
#  'Analytics_PublicFunctionArrayArg',
#  'Analytics_ERC20TransferCall',
#  'Analytics_ERC20TransferFromCall',
#  'Analytics_ERC20ApproveCall',
]

analytics = [
  'decomp_time',
  'client_time',
  'Analytics_JumpToMany'
]

decomp_analytics = [
  'Analytics_ReachableBlocks',
  'Analytics_UnreachableBlock',
  'Analytics_ReachableBlocksInTAC',
  'Analytics_BlockHasNoTACBlock',
  'Analytics_DeadBlocks',
  'Analytics_PolymorphicTargetSameCtx',
#  'Analytics_MissingJumpTargetAnyCtx',
#  'Analytics_LocalBlockEdge',
#  'Analytics_JumpToManyWithoutGlobalImprecision',
#  'Analytics_Blocks',
#  'Analytics_Contexts',
#  'Analytics_JumpToManyWouldHaveBeenCloned',
#  'Analytics_JumpToManyNonPopBlock',
]

mem_analytics = [
  'Analytics_NonModeledMSTORE',
  'Analytics_NonModeledMLOAD',
  'Analytics_PublicFunctionArg',
  'Analytics_PublicFunctionArrayArg'
]

storage_analytics = [
  'Analytics_NonModeledSSTORE',
  'Analytics_NonModeledSLOAD',
  'Analytics_GlobalVariable',
# 'Analytics_UselessSLOAD',
]

list_of_verbatim_rels = {
  'Verbatim_BlocksReachabilityMetric'
}


parser = argparse.ArgumentParser(
                    prog='Compare Runs',
                    description='Compares multiple runs of gigahorse.py using the produced json files')

parser.add_argument('result_files', nargs='*')
parser.add_argument('-v', '--verbose', action='store_true')
parser.add_argument('-d', '--decomp', action='store_true',
                    help='Includes core decompilation specific relations and analytics')
parser.add_argument('-m', '--memory', action='store_true',
                    help='Includes memory modeling specific relations and analytics')
parser.add_argument('-s', '--storage', action='store_true',
                    help='Includes storage modeling specific relations and analytics')

parser.add_argument('--point_to_point', type=str)

args = parser.parse_args()

def process_result_file(filename, output_set=None):
    filemap = dict()

    for rel in rels:
        filemap[rel] = set()

    for analytic in analytics:
        filemap[analytic] = 0
    filemap['has_output'] = set()
    filemap['timeout'] = set()

    relset = set(rels)
    with open(filename) as json_file:
        data = json.load(json_file)
        for contract in data:
            name = contract[0].replace('.hex', '')
            have_output = set(contract[1])
            client_success = "CLIENT TIMEOUT" not in contract[2]

            filemap[name] = dict()
            filemap[name]["rels"] = have_output
            filemap[name]["analytics"] = contract[3]
            if output_set and name not in output_set:
                continue
            if have_output and client_success:
                filemap['has_output'].add(name)
            else:
                filemap['timeout'].add(name)

            for rel in relset & have_output:
                #print(f'contract {name} has vuln {vuln}')
                filemap[rel].add(name)

            for analytic in analytics:
                if analytic in contract[3]:
                    filemap[analytic] += contract[3][analytic]

            #break
    return filemap

if args.decomp:
    analytics += decomp_analytics

if args.memory:
    analytics += mem_analytics

if args.storage:
    analytics += storage_analytics

result_files = args.result_files

result_files_simple = [Path(file).stem for file in result_files]

results_processed = [process_result_file(file) for file in result_files]

has_out = [res['has_output'] for res in results_processed]

has_timeout = [res['timeout'] for res in results_processed]

output_in_any = set.union(*has_out)

output_in_all = set.intersection(*has_out)

timeout_in_all = set.intersection(*has_timeout)

results_processed_common = [process_result_file(file, output_in_all) for file in result_files]

print(f"{len(timeout_in_all) + len(output_in_any)} total contracts")
print(f"{len(output_in_any)} contracts decompiled/analyzed by some config")
print(f"{len(output_in_all)} contracts decompiled/analyzed by all configs \033[1m(common)\033[0m")


if len(result_files) == 2:
    for rel in rels + ['has_output']:
        not_in_file1 = results_processed[1][rel] - results_processed[0][rel]
        not_in_file2 = results_processed[0][rel] - results_processed[1][rel]
        print(len(results_processed[0][rel]), len(results_processed[1][rel]))
        print(f'\n\nFor {rel} {len(not_in_file1)} not detected by config {result_files_simple[0]}: {not_in_file1}')
        print(f'For {rel} {len(not_in_file2)} not detected by config {result_files_simple[1]}: {not_in_file2}')

for analytic in analytics:
    print(f'\n\033[1mANALYTIC: {analytic}\033[0m')
    for i in range(0, len(result_files)):
        print(f'{result_files_simple[i]}: {results_processed[i][analytic]}')

    for i in range(0, len(result_files)):
        print(f'{result_files_simple[i]} \033[1m(common)\033[0m: {results_processed_common[i][analytic]}')


if args.point_to_point:
    print(args.point_to_point)
    format_row = "{:>30}" * (len(result_files_simple) + 2)
    print(format_row.format("", *(["Contract"] + result_files_simple)))
    for file in output_in_all:
        print(format_row.format("", *([file] + [res[file]["analytics"][args.point_to_point] for res in results_processed_common])))