from __future__ import print_function, absolute_import

class dispatcher:
    def __init__(self, name=None):
        '''
        Creates a new event dispatcher.
        The optional name argument is for convenience - to let one tell handlers
        of the same class apart.
        '''
        self.name = name or self.__class__.__name__
        self.handlers = []

    def add(self, handler):
        '''
        Appends the given handler to the list of handlers.
        On dispatch, the handler will be called with the event object and the
        result will replace it in the list. If it returns None, it is removed
        from the list of handlers.
        '''
        self.handlers.append(handler)

    def dispatch(self, event):
        '''
        Calls each handler with the event object and replaces that handler
        in the list of handlers with the return value. If the handler
        returns None, it is removed.
        The event object must have a 'type' attribute set.
        '''
        self.handlers[:] = [new_handler
                            for new_handler in (handler(event) for handler in self.handlers)
                            if new_handler is not None]

