from ..args import subcommand, argument

args = []

args.append(argument(
    '-H', '--hashes',
    default=None,
    help="path to a file containing hashes. Format: "
         "'<UPN suffix>\\<account name>:<id>:<lm hash>:<nt hash>:::'",
))

args.append(argument(
    '-A', '--accounts-plus-passwords',
    default=None,
    help="path to a file with the results from the `ntlm` subcommand. "
         "Format: '<account name>:<password>'",
))

args.append(argument(
    '-P', '--passwords-only',
    default=None,
    help="path to a file with only passwords; one per line",
))

args.append(argument(
    '-F', '--filter-accounts',
    default=None,
    help="""
path to a file containing names of accounts which are subject to analysis,
all other accounts will be filtered out (Example: only active accounts,
only kerberoastable accounts, etc.). If empty, all accounts will be
subject to analysis. Format: one per line, without domain or UPN suffix,
case insensitive.
"""
))

args.append(argument(
    '-c', '--censor',
    action='store_true',
    default=False,
    help="only output statistics without sensitive information "
         "(default: %(default)s)",
))

args.append(argument(
    '-f', '--format',
    choices=['text', 'json'],
    default='text',
    help="output format (default: %(default)s)",
))

args.append(argument(
    '-o', '--outfile',
    default=None,
    help="path to an output file (default: stdout)",
))


@subcommand(args)
def analytics(args):
    '''Output interesting statistics'''
    from ..analytics import create_report
    from ..asciioutput import pretty_print

    report = create_report(
        args.hashes,
        args.accounts_plus_passwords,
        args.passwords_only,
        args.filter_accounts,
        censor=args.censor,
    )

    if not report:
        exit(1)

    if args.format == 'json':
        import json
        out = json.dumps(report, indent=4)
    elif args.format == 'text':
        out = pretty_print(report['report'])
        out += pretty_print(report['sensitive'])

    if args.outfile:
        with open(args.outfile, 'w') as f:
            f.write(out)
    else:
        print(out, end='')
