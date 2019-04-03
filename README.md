# email_manager

## Intro 

This small application has been designed with one goal and only one goal:
    **delete emails**

If you are like me:
- You have several emails accounts
- Some accounts might be _very_ old
- You are receiving tons and tons of useless emails
- You never clean your emails

But even if you don't need them, those emails are stored somewhere.
They consumme memory and energy for basically nothing.

So I decided to make a small application to target and delete them easily.

This application will allow you to:
- Check how many emails are _sleeping_ in your account
- Summarize them by sender
- Search for emails and display a summary of each emails
- Read those emails
- Delete email individually or by batch
- See what a buggy application looks like

There's probably some other applications that will allow you to do the above
stuff much faster and easily than my application, but hey it's working and I
want to share it anyway !

On the plus side I found it very interesting to be able to see from who 
were my biggest spammers.


## Installation

To run this application, you only need python3. I made sure to only use
package from the standard librairy.

Just clone or download the repository on your computer and run main.py with python3.

You will need to insert your login information in the config.ini file.
Note that you can store several logins in that file.

Once connected, I advise you to run the following command:
- -b     will list all your available mailboxes and the number of emails in each of them
- -ts    will download all emails in your current mailbox and make a summary by sender

Note that the application will automatically log you in the mailbox which contains the most emails

Some technical details on the application itself:

It will download emails by using threads. In the config file, you can
choose how many connections should be opened at the same time.

Downloaded emails will be stored in a cache (only the headers information though).
Content won't be stored in cache and will only be downloaded when reading an email.


## Issues you might encounter

### Slowliness

If like me you need to download or delete several thousands of emails, it might
take some time.

I've made sure to speed up the process where I could but it's far from being
perfect and I will spend time to improve speed in the future.

I added a progress bar to let you know of any task advancement.

You might also be slowed down by your provided if you download too much data

### Bugs

I could not test the application on all email providers.
It should correctly work on gmail, microsoft (outlook, hotmail...) though.
I hope it will be working correctly on other provider too but I cannot say for sure.

In any case there are still some bugs everywhere so just be indulgent and let me know
of any bug you might encounter if you are willing to help me :)


### Cached emails in duplicates

IMAP does not allow to uniquely identify emails in different mailboxes.
Meaning that a same email will have a different ID depending on the mailbox.
Meaning that when you delete one email from a specific mailbox, it might still
show by looking at emails from another mailbox because of the cache on your local machine.

This is a local issue only (the email is correctly deleted from the server)
and it's caused by the way the application manages the cache, which is shitty
because I haven't been able to find a way to link same emails in
their different mailboxes.

You just need to be aware of the issue and regulary delete the cache (there's
an option for that)


## Feedback
Don't hesitate to leave me any feedback, good or bad.
Nothing will make me happier than receiving feedback :)

