class Singleton(object):
    """单例类"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance


if __name__ == '__main__':
    class MySingleton(Singleton):
        pass


    a = MySingleton()
    b = MySingleton()

    assert a is not b
