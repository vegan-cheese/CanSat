class PartiallyReceivedData:
    pass

already_finished_timestamps: list[int] = []
cache: list[PartiallyReceivedData] = []

def onReceivedData():
    pass
    # Check if it is our team's message

    # Check timestamp
    """
    if timestamp in cache:
        check if the piece of data being received has not been received yet
        if it hasn't:
            add it in
        if it has:
            ignore

    check if all pieces of data are satisfied for the data of this timestamp:
    if yes:
        remove from cache
        save to (whatever we are saving to)
    if no:
        if it has been 3 seconds since time on timestamp then
            send resend message for missing data
    """
ls = [1,2,3,4,5,6,7]
for num in ls:
    if num == 3:
        num.
print(ls)