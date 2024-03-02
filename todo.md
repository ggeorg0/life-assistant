# Plugins
- move some funcs from tools to `AbstractPlugin`
- [ ] Use time instead of datetime in daily events
          (don't foget to update UniSchedule and others)
- [X] Plugin ON and OFF commands
- [X] Process is plugin enabled or not
- [ ] Reload plugins with user command

## InboxManagement
- [x] Fix TODO: move code from my Notion class to plugin methods
- [ ] Check imports

## MorningSummary
- [X] Rewrite with new architecture

## UniSchedule
- [ ] Add day argument to /schedule:
        /schedule 0  - today
        /schedule 1  - tomorrow
        /schedule -1  - yesterday

# Bot
- [X] Delete comments
- [X] Replace "Remind Me" with Timer plugin

### Misc
- [ ] Remove postgresql from `requirements.txt`
- [ ] Add `Readme.md`
- [ ] Update or remove `main.py` file (useless)

# Readme
#### not exists yet

# Future:
- [ ] Delete past events from calendar
- [ ] Advanced Logging (fix loggin levels, remove INFO for httpx)
