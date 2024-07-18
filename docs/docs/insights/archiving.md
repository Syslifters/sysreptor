# Archiving
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

This page describes how SysReptor archives and encrypts old pentest projects.
It gives an overview of the cryptographic architecture used to protect archives and explains the motivations behind.


## Motivation - Why do we need to archive pentest projects?
As a penetration tester, you know how important it is to keep your pentest data safe and secure. 
It contains highly sensitive data such as vulnerabilities of customer systems and how to exploit them. 
Sometimes it takes some time to fix the vulnerabilities (or they marked it as "risk accepted").
It's crucial to safeguard pentest reports and pentest data to protect your customer's systems from malicious actors.
In fact, you may even have signed an NDA or be subject to contractual penalties if this data is stolen, leaked, or published.

But what happens when a pentest is completed and you no longer need to access that data on a regular basis?
The most secure option is to delete all data associated with the pentest.
However, this is often not possible.
The report and pentest evidence (e.g. burp state, command history, scripts, etc.) have to be kept for the purposes of proof of work and warranty.

Old pentest data should not be stored in plaintext. Instead they should be encrypted.
Restricting access with a permissions is not sufficient,
since a system administrator or service provider, for example, could also have access to the data.
Access restrictions must be enforced through the use of cryptography.

When encrypting pentest data, the question araises who will be able to decrypt the archive again?
Balancing confidentiality with availability is an important question.
Here are some thoughts to consider:

* Data is secure if no one can decrypt it anymore: This is certainly true, but it's important to remember that encryption is only one aspect of data security. 
  There are other factors to consider, such availability.
  If no one can decrypt the data, it may become unavailable when it's needed, which can be a problem.
* What happens if someone leaves the company or loses the key? 
    * If one key is used to encrypt all pentest archives, this key may not get lost. Else all data is inaccessible.
    * If a different key is used to encrypt pentest archives (i.e. one key per archive), and they are all managed by the same person (e.g. in a password manager) and this person leaves the company, forgets the master key or dies. Again, everything is lost.
    * If archives are encrypted with multiple keys and these keys are distributed to different persons, when one person loses their key, you have the same problem. And once again, everything is lost.
* Should one person be able to decrypt everything alone? 
  To prevent unavailability through key loss, you can give the key to multiple persons.
  Or you can also design an archiving system where each pentest archive is encrypted with multiple keys and each key is given to a different person.
  Now everyone is able to decrypt all data on their own.

Consider you are a pentesting team of four persons. 
The optimal compromise between confidientiality and availablity of pentest archives would be to require two persons to access pentest archives.
This prevents losing all data when one person (or even a second person) loses their key.
It also prevents everyone from accessing all data (e.g. if a key is compromizes or someone leaves the company and wants to steals all data) alone.
At least two persons are required, thus enforcing a 4-eye principle.



## Crypto Architecture
We use a threshold cryptography scheme in combination with key management based on public key cryptography to cryptographically enforce the 4-eye principle.

The core component to cryptographically enforce the 4-eye principle is Shamir Secret Sharing.
Shamir Secret Sharing is a threshold sheme for sharing a secret to a group of _n_ people whereas _k_ people are required to work together to reconstruct the secret.
The secret is split into _n_ shares and every user is given one share. The threshold _k_ defines how many shares are required to reconstruct the secret. 
Shamir Secret Sharing has the property of information-theoretic security, meaning that even if an attacker steals some shares, it is impossible for the attacker to reconstruct the secret unless they have stolen _k_ number of shares. No information about the secret can be gained from any number of shares below than the threshold

In order to enforce a 4-eye principle to restore encrypted pentest archives, the threshold needs to be _k=2_.
However it is possible to increase the threshold _k_ to require 3 or more users for restoring pentest archives for larger companies.

Shamir Secret Sharing only allows splitting secrets into shares. It does not handle encryption or key management.
We use Shamir Secret Sharing for splitting an AES-Key into multiple Key Shares.
Each Key Share is assigned to a different user.

Key Shares are encrypted with user's public keys.
The private keys are managed offline by users themselves.
You can use software keys generated on your computer, but also security tokens such as YubiKeys that generate keys on hardware.
Public-key cryptography allows users to create pentest project archives where multiple users have access, without requiring user interaction.
For decrypting, user interaction is required. Each user has to decrypt their own Shamir Key Share with their private key.

We use OpenPGP for public key encryption, because it supports RSA and elliptic curves and offers support for hardware tokens such as YubiKeys.
OpenPGP is a secure, established and trustworthy crypto protocol with great tooling support.
It is more user-friendly than using plain openssl and YubiKey CLI tools, and more trustworthy than custom developed crypto tools.

Offloading cryptographic operations to hardware tokens such as YubiKeys is considered more secure than using software based encryption, 
because the secret key is generated on hardware and never leaves the device.
This prevents the private key from being leaked or exported.
The downside, however, is that it cannot be backed up. If you lose the hardware token, the encrypted data is inaccessible.
This is why we support multiple public/private key pairs per user. 
For example if you use two public keys stored on hardware tokens and if you lose one, you can still restore archives with the second one.


Following diagram outlines the process of archiving and encrypting a pentest project:
![Archive and encrypt pentest project](../../images/archiving-crypto.drawio.png)


1. Export all project data to a tar.gz archive.
   This is the same format as directly exporting projects via the web interface.
   All project data, sections, findings, notes, images, files including the design are exported.
2. The tar.gz archive is encrypted with 256-bit AES-GCM. A random key is generated for each archive.
   AES-GCM is an authenticated cipher mode (AEAD). Besides encrypting the data, a authentication tag is calculated which is able to detect modifications and corruptions of encrypted data, adding integrity-protection of the ciphertext.
   The encrypted archive is stored in a file storage ([ARCHIVED_FILE_STORAGE](../../setup/configuration#archiving)).
3. The AES-key is distributed to multiple users with Shamir Secret Sharing.
4. The Key Shares are encrypted with randomly generated 256-bit AES-GCM keys. Each Key Share is encrypted with a different key.
   Plain Shamir Secret Sharing does not offer integrity-protection of Key Shares and does not detect if a Key Share used for decryption is valid or not. 
   This step adds integrity protection of Key Shares with the AES-GCM (and confidentiality protection with encryption).
   The encrypted Key Shares are stored in the database.
5. The AES keys are encrypted with user's public keys.
   


## How to use

### Prerequisite: Register user public keys
Before users are able to archive pentest projects, all archiving users have to register their public keys.
Public Keys need to be generated offline and uploaded to the user profile.

SysReptor uses OpenPGP encryption keys as the public key format. 
RSA and elliptic curve keys are supported.
Minimum key lengths are enforced to ensure a sufficient security level for some years.
For RSA, the minimum accepted key length is 3072 bit.
For elliptic curve, the minium curve size is 256 bit.

=== "Generate private keys with GPG"

    Use following commands to generate an elliptic curve encryption key with `gpg`. 
    Be sure to protect the key with a strong password and make backups.
    If you lose all your private keys, you can no longer restore archives.

    ```
    cat << EOF > config.txt
    Key-Type: ECDSA
    Key-Curve: nistp521
    Subkey-Type: ECDH
    Subkey-Curve: nistp521
    Subkey-Usage: encrypt
    Expire-Date: 0
    Name-Comment: SysReptor Archiving
    Name-Real: <your name>
    Name-Email: <your email>
    EOF
    gpg --batch --generate-key config.txt

    gpg --list-secret-keys --keyid-format=long
    gpg --armor --export <key-id>
    ``` 

=== "Generate private keys on YubiKey 5"

    Use the following command to generate a new Elliptic Curve key pair on a YubiKey 5.
    The private key is generated on the YubiKey and never leaves the device.
    Beware that you cannot backup the key. We recommend that you add a second key as a fallback in case you lose your YubiKey.


    ```
    gpg --card-edit
                            
    Reader ...........: Yubico YubiKey FIDO CCID 00 00
    Application ID ...: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    Application type .: OpenPGP
    Version ..........: 3.4
    Manufacturer .....: Yubico
    Serial number ....: 19763721
    Name of cardholder: [not set]
    Language prefs ...: [not set]
    Salutation .......:
    URL of public key : [not set]
    Login data .......: [not set]
    Signature PIN ....: not forced
    Key attributes ...: rsa2048 rsa2048 rsa2048
    Max. PIN lengths .: 127 127 127
    PIN retry counter : 3 0 3
    Signature counter : 0
    KDF setting ......: off
    UIF setting ......: Sign=off Decrypt=off Auth=off
    Signature key ....: [none]
    Encryption key....: [none]
    Authentication key: [none]
    General key info..: [none]

    gpg/card> admin
    Admin commands are allowed

    # Change Yubikey Pin (optional)
    # Hint: default pin is 123456, default admin pin is 12345678
    gpg/card> passwd
    gpg: OpenPGP card no. XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX detected

    1 - change PIN
    2 - unblock PIN
    3 - change Admin PIN
    4 - set the Reset Code
    Q - quit

    Your selection? 3
    PIN changed.

    1 - change PIN
    2 - unblock PIN
    3 - change Admin PIN
    4 - set the Reset Code
    Q - quit

    Your selection? 1
    PIN changed.

    1 - change PIN
    2 - unblock PIN
    3 - change Admin PIN
    4 - set the Reset Code
    Q - quit

    Your selection? Q

    gpg/card> name
    Cardholder's surname: <your name>
    Cardholder's given name: <your name>

    # Change key type to elliptic curve (optional)
    gpg/card> key-attr
    Changing card key attribute for: Signature key
    Please select what kind of key you want:
       (1) RSA
       (2) ECC
    Your selection? 2
    Please select which elliptic curve you want:
       (1) Curve 25519 *default*
       (4) NIST P-384
    Your selection? 1
    The card will now be re-configured to generate a key of type: ed25519
    Note: There is no guarantee that the card supports the requested
          key type or size.  If the key generation does not succeed,
          please check the documentation of your card to see which
          key types and sizes are supported.
    Changing card key attribute for: Encryption key
    Please select what kind of key you want:
       (1) RSA
       (2) ECC
    Your selection? 2
    Please select which elliptic curve you want:
       (1) Curve 25519 *default*
       (4) NIST P-384
    Your selection? 1
    The card will now be re-configured to generate a key of type: cv25519
    Changing card key attribute for: Authentication key
    Please select what kind of key you want:
       (1) RSA
       (2) ECC
    Your selection? 2
    Please select which elliptic curve you want:
       (1) Curve 25519 *default*
       (4) NIST P-384
    Your selection? 1
    The card will now be re-configured to generate a key of type: ed25519

    # Generate key pair
    gpg/card> generate
    Make off-card backup of encryption key? (Y/n) n
    Please specify how long the key should be valid.
    0 = key does not expire
        <n>  = key expires in n days
       <n>w = key expires in n weeks
       <n>m = key expires in n months
       <n>y = key expires in n years
    Key is valid for? (0) 0
    Key does not expire at all
    Is this correct? (y/N) y

    GnuPG needs to construct a user ID to identify your key.

    Real name: <your name>
    Email address: <your email>
    Comment: SysReptor Archiving Key
    You selected this USER-ID:
    "<your name> (SysReptor Archiving Key) <your email>"

    Change (N)ame, (C)omment, (E)mail or (O)kay/(Q)uit? O
    public and secret key created and signed.

    gpg/card> quit

    gpg --list-secret-keys --keyid-format=long
    gpg --armor --export <key-id>
    ```


During public key registration, you have to prove that you own the private key.
A random verification message is generated and encrypted with the public key.
You have to decrypt it with your private keys to prove that you own the private key and know how to decrypt data.



### Archive Project
Pentest projects first have to be marked as finished, then they can be archived.

Before the archive is created and encrypted, all users are displayed that will have access to the archive and are able to restore it.
This includes all project members and global archivers.
Global archivers are added to every archived project and can be considered archiving backup users.
Users can be marked as global archivers in the user permission settings.

If too few users (below threshold) are project members or global archivers or do not have any public keys, archiving is not possible.

![Archive project](../../images/archive-create.png)


### Restore Archived Projects
Archived projects are restored when the required number of users decrypt their key share with their private keys.
Users decrypt their key shares separately, independently of each other. 
When the user threshold is reached, the archived project is restored.

![Restore archived project](../../images/archive-restore.png)
![Restore archived project](../../images/archive-restore2.png)

All users should restore their key parts within 3 days.
When some users decrypted their key shares, but others did not, the archive is reset. 
Decrypted key shares are deleted, meaning that users have to decrypt their key shares again later with their public keys.
This prevents partly dearchived projects being stored in the database forever, lowering the required user threshold when archives are actually restored.


### Threshold Recommendations
The recommended Shamir Secret Sharing threshold _k_ is about half the number of users _n_, but at least 2.
This ensures the best combination of confidentiality and availability.
For large teams (e.g. >5 global archivers), you might want to use a _k_ below _n / 2_ to not require as many users for restoring archives.

Note that not every user is added to an archive.
Only project members and global archivers with public keys are added to archives and are able to access them.

Example: You are a large pentesting company with 100 users. 
A finished project should be archived, where 3 pentesters are project members.
Only the 3 project members and (lets say) 2 global archivers will be added to the archive.

Our recommendations:

* _n = 1_ users: _k = 1_ recommended
* _n = 2_ users: _k = 1_ or _k = 2_ recommended
* _n = 3_ users: _k = 2_ recommended
* _n = 4_ users: _k = 2_ recommended
* _n = 5_ users: _k = 2_ recommended
* _n = 10_ users: _k = 3_ or _k = 4_ recommended 

The threshold value is configured globally per instance by the settings [ARCHIVING_THRESHOLD](../../setup/configuration#archiving).
