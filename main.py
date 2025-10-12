from src.crawler_manager import CrawlerManager
import socket


def main():
    crawler = CrawlerManager()
    crawler.run()

if __name__ == "__main__":
    old_getaddrinfo = socket.getaddrinfo
    def new_getaddrinfo(*args, **kwargs):
        responses = old_getaddrinfo(*args, **kwargs)
        return [response for response in responses if response[0] == socket.AF_INET]
    socket.getaddrinfo = new_getaddrinfo

    main()