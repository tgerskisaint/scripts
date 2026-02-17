from python_cron import Cron

def water_reminder():
    while True:
        print("Sip water or die hoe")

cron = Cron()
cron.schedule('* * * * *', water_reminder)
cron.start()
