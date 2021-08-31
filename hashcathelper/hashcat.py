"""Interface with hashcat"""

import logging
import pkgutil
import subprocess
import sys
import tempfile

log = logging.getLogger(__name__)

NT_RULESET = pkgutil.get_data(__name__, 'toggles-lm-ntlm.rule')


def prepend_usernames(wordlists, hashfile, directory='.'):
    """Extract usernames from hashfile, write to a temporary file, and
    prepend it to list of wordlists
    """
    from hashcathelper.utils import parse_user_pass

    user_file = tempfile.NamedTemporaryFile(
        delete=False, dir=directory, mode='w',
        prefix='userlist_',
    )
    with open(hashfile, 'r') as fp:
        for line in fp.readlines():
            username = parse_user_pass(line)['username']
            # Warning: hashfile is not actually meant to be parsed by
            # parse_user_pass. Password will now contain user ID, LM hash
            # and NT hash, but that's fine here.
            # Also, username is converted to lower case by that function.
            user_file.write(username + '\n')
    user_file.close()
    wordlists.insert(0, user_file.name)


def hashcat(hashcat_bin, hashfile, hashtype, wordlists=[], ruleset=None,
            pwonly=True, directory='.'):
    """
    Run hashcat as a subprocess

    Returns: name of a file containing the stdout of hashcat with ``--show``
    """

    base_command = [
        hashcat_bin,
        hashfile,
        '--username',
        '-m', str(hashtype),
    ]
    command = base_command + ['--outfile-autohex-disable']
    if wordlists:
        prepend_usernames(wordlists, hashfile, directory=directory)
        command = command + ['-a', '0'] + wordlists
        # Attack mode wordlist
        if ruleset:
            command = command + ['-r', ruleset]
    else:
        # Attack mode brute force, all combinations of 7 character passwords
        # (This assumes cracking LM hashes)
        command = command + ['-a', '3', '-i', '?a?a?a?a?a?a?a',
                             '--increment-min', '1', '--increment-max', '7']

    log.debug("Running this command: %s" % command)
    p = subprocess.Popen(
        command,
        stdout=sys.stdout,
        stderr=subprocess.STDOUT,
    )
    p.communicate()
    if p.returncode:
        raise RuntimeError("Hashcat exited with non-zero return code")

    # Retrieve result
    show_command = base_command + ['--show']
    show_command += ['--outfile-format', '2']

    p = subprocess.Popen(
        show_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    passwords, _ = p.communicate()
    if p.returncode:
        raise RuntimeError(
            "Hashcat exited with non-zero return code when retrieving result"
        )

    result = tempfile.NamedTemporaryFile(delete=False, dir=directory)
    for p in passwords.splitlines():
        if pwonly:
            # Remove username
            p = b':'.join(p.split(b':')[1:])
        # Write rest of the line to the result file
        result.write(p + b'\n')
    result.close()
    return result.name


def crack_pwdump(hashcat_bin, hashfile, directory, wordlist, ruleset,
                 extra_words=[], skip_lm=False):
    """
    Crack the hashes in a pwdump file.

    Files like this are generated by Impacket's secretsdump or Meterpreter's
    pwdump, for example. A line looks like this:

        <USER NAME>:<USER ID>:<LM HASH>:<NT HASH>:::

    First, the LM hashes are cracked in incremental mode. Then, the results
    are used with an NTLM rule set to crack the corresponding NT hashes.
    Last, the results are added to the crackstation wordlist and mangled
    with the OneRule rule set.
    """

    if skip_lm:
        log.info("Skipping LM hashes")
        wordlists = [wordlist]
    else:
        lm_result = hashcat(
            hashcat_bin,
            hashfile,
            hashtype=3000,
            directory=directory,
        )

        # Write ruleset to file in tempdir
        nt_ruleset = tempfile.NamedTemporaryFile(
            'wb',
            dir=directory,
            delete=False,
            prefix='rules_',
        )
        nt_ruleset.write(NT_RULESET)
        nt_ruleset.close()

        nt_result = hashcat(
            hashcat_bin,
            hashfile,
            hashtype=1000,
            ruleset=nt_ruleset.name,
            wordlists=[lm_result],
            directory=directory,
        )
        wordlists = [nt_result, wordlist]

    final_result = hashcat(
        hashcat_bin,
        hashfile,
        hashtype=1000,
        ruleset=ruleset,
        wordlists=wordlists,
        pwonly=False,
        directory=directory,
    )
    return final_result
