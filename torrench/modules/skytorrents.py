"""SkyTorrents Module."""
import sys
import logging
from torrench.utilities.Config import Config


class SkyTorrents(Config):
    """
    SkyTorrents class.

    This class fetches torrents from SKY website,
    and diplays results in tabular form.
    Further, torrent's magnetic link,
    upstream link and files to be downloaded with torrent can be
    printed on console.
    Torrent can be added to client directly

    This class inherits Config class. Config class inherits
    Common class. The Config class provides proxies list fetched
    from config file. The Common class consists of commonly used
    methods.

    All activities are logged and stored in a log file.
    In case of errors/unexpected output, refer logs.
    """

    def __init__(self, title, page_limit):
        """Initialisations."""
        Config.__init__(self)
        self.proxies = self.get_proxies('sky')
        self.title = title
        self.pages = page_limit
        self.logger = logging.getLogger('log1')
        self.index = 0
        self.page = 0
        self.total_fetch_time = 0
        self.mylist = []
        self.mapper = []
        self.soup_dict = {}
        self.soup = None
        self.output_headers = ["NAME  ["+self.colorify("green", "+UPVOTES")+"/"+self.colorify("red", "-DOWNVOTES")+"]",
                               "INDEX", "SIZE", "FILES", "UPLOADED", "S/L"]
        ######################################
        self.top = "/top1000/all/ed/%d/?l=en-us" % (self.page)
        self.file_count = 0

    def check_proxy(self):
        """
        To check proxy (site) availability.

        Though skytorrents (as of now) is only using the
        main site, the function is named as check_proxy to
        confirm uniformity across modules.
        In case of failiur, program exits.
        """
        try:
            count = 0
            for proxy in self.proxies:
                print("Trying %s" % (self.colorify("yellow", proxy)))
                self.logger.debug("Trying proxy: %s" % (proxy))
                """
                Performing test for string hello.
                """
                self.logger.debug("Carrying out test for string 'hello'")
                self.soup = self.http_request(proxy + "/search/all/ed/1/?l=en-us&q=hello")
                if self.soup.find_all('tr')[1] is None or self.soup is None or self.soup == -1:
                    print("Bad proxy!")
                    count += 1
                    if count == len(self.proxies):
                        self.logger.debug("Proxy list finished! Exiting!")
                        print("No more proxies found! Exiting...")
                        sys.exit(2)
                else:
                    self.logger.debug("Passed! Connected to proxy!")
                    print("Available!")
                    self.proxy = proxy
                    break
        except Exception as e:
            print("Error message: %s" %(e))
            print("Something went wrong! See logs for details. Exiting!")
            self.logger.exception(e)
            sys.exit(2)

    def get_top_html(self):
        """To get top 1000 torrents."""
        print(self.colorify("green", "\n\n*Top 1000 SkyTorrents*"))
        print("1000 Torrents are divided into 25 pages (1 page = 40 torrents)\n")
        try:
            option = int(input("Enter number of pages (0<n<=25): "))
            if option <= 0 or option >= 25:
                print("Bad input! Exiting!")
                sys.exit(2)
            else:
                self.pages = option
        except ValueError as e:
            print("Bad input! Exiting!")
            self.logger.exception(e)
            sys.exit(2)

    def get_html(self):
        """
        To get HTML page.

        Once proxy is found, the HTML page for
        corresponding search string is fetched.
        Also, the time taken to fetch that page is returned.
        Uses http_request_time() from Common.py module.

        Also, TOP torrents search is resolved here.
        The variable [search] is set accordingly.
        If --top is used, title is set to None. This is the condition
        checked for --top.
        """
        try:
            for self.page in range(self.pages):
                print("\nFetching from page: %d" % (self.page+1))
                self.logger.debug("fetching page %d/%d" % (self.page+1, self.pages))
                """
                If title is none, get TOP torrents.
                """
                if self.title is None:
                    search = "/top1000/all/ed/%d/?l=en-us" % (self.page+1)
                else:
                    search = "/search/all/ed/%d/?l=en-us&q=%s" % (self.page+1, self.title)
                self.soup, time = self.http_request_time(self.proxy + search)
                print("[in %.2f sec]" % (time))
                self.logger.debug("page fetched in %.2f sec!" % (time))
                self.total_fetch_time += time
                self.soup_dict[self.page] = self.soup
        except Exception as e:
            print("Error message: %s" %(e))
            print("Something went wrong! See logs for details. Exiting!")
            self.logger.exception(e)
            sys.exit(2)

    def parse_html(self):
        """
        Parse HTML to get required results.

        Results are fetched in masterlist list.
        Also, a mapper[] is used to map 'index'
        with torrent name, link and magnetic link
        and files_count (counts number of files torrent has)
        """
        masterlist = []
        try:
            for page in self.soup_dict:
                self.soup = self.soup_dict[page]
                content = self.soup.find_all("tr")
                for i in range(len(content)):
                    if i == 0:
                        continue
                    data = content[i]
                    results = data.find_all("td")
                    name = results[0].find_all('a')[0].string
                    name = name.encode('ascii', 'replace').decode()
                    upvotes = '0'
                    downvotes = '0'
                    try:
                        upvotes = str(results[0]).split("\xa0")[1].replace(" ", "").split("<")[0]
                    except IndexError as e:
                        self.logger.exception(e)
                        pass
                    try:
                        downvotes = str(results[0]).split("\xa0")[2].replace(" ", "").split("<")[0]
                    except IndexError as e:
                        self.logger.exception(e)
                        pass
                    upvotes = self.colorify("green", ("+"+upvotes))
                    downvotes = self.colorify("red", ("-"+downvotes))
                    display_votes = "  [%s]" % (upvotes+"/"+downvotes)
                    link = results[0].find_all('a')[0]['href']
                    magnet = results[0].find_all('a')[1]['href']
                    size = results[1].string
                    self.file_count = results[2].string
                    uploaded = results[3].string
                    seeds = results[4].string
                    leeches = results[5].string
                    self.index += 1

                    self.mapper.insert(self.index, (name, magnet, link, self.file_count))
                    #self.mylist = [name + "["+str(upvotes)+"/"+str(downvotes)+"]", "--"+str(self.index)+"--", size, self.file_count, uploaded, seeds, leeches]
                    self.mylist = [name + display_votes,
                            "--"+str(self.index)+"--", size, self.file_count,
                            uploaded, (seeds + '/' + leeches)]
                    masterlist.append(self.mylist)

            if masterlist == []:
                print("No results found for given input!")
                self.logger.debug("No results found for given input! Exiting!")
                sys.exit(2)
            self.logger.debug("Results fetched successfully!")
            self.show_output(masterlist, self.output_headers)
        except Exception as e:
            print("Error message: %s" %(e))
            print("Something went wrong! See logs for details. Exiting!")
            self.logger.exception(e)
            sys.exit(2)

    def after_output_text(self):
        """
        After output is displayed, Following text is displayed on console.

        Text includes instructions, total torrents fetched, total pages,
        and total time taken to fetch results.
        """
        oplist = [self.index, self.total_fetch_time]
        self.after_output('sky', oplist)

    def select_torrent(self):
        """
        To select required torrent.

        Torrent is selected through index value.
        Prints magnetic link and upstream link and torrent files present
        to console.
        Also, torrent can be added directly to client
        (Note: Might not work as expected.)
        """
        self.logger.debug("Selecting torrent...")
        temp = 9999
        while(temp != 0):
            try:
                temp = int(input("\n(0=exit)\nindex > "))
                self.logger.debug("selected index %d" % (temp))
                if temp == 0:
                    print("\nBye!")
                    self.logger.debug("Torrench quit!")
                    break
                elif temp < 0:
                    print("\nBad Input!")
                    continue
                else:
                    selected_torrent, req_magnetic_link, torrent_link, self.file_count = self.mapper[temp-1]
                    selected_torrent = self.colorify("yellow", selected_torrent)
                    print("\nSelected index [%d] - %s\n" % (temp, selected_torrent))
                    self.logger.debug("selected torrent: %s ; index: %d" % (selected_torrent, temp))

                    # Show torrent files?
                    option = input("Show torrent files? [y/n]: ")
                    self.logger.debug("View torrent files: [%s]" % (option))
                    if (option == 'y' or option == 'Y'):
                        self.show_files(torrent_link)
                        self.logger.debug("Torrent files displayed.")
                    elif (option == 'n' or option == 'N' or option == ""):
                        self.logger.debug("Torrent files NOT displayed.")

                    # Print Magnetic link / load magnet to client
                    temp2 = input("\n1. Print magnetic link [p]\n2. Load magnetic link to client [l]\n\nOption [p/l]: ")
                    temp2 = temp2.lower()
                    self.logger.debug("selected option: [%c]" % (temp2))
                    if temp2 == 'p':
                        self.logger.debug("printing magnetic link and upstream link")
                        print("\nMagnet link: {magnet}".format(magnet=self.colorify("red", req_magnetic_link)))
                        self.copy_magnet(req_magnetic_link)
                        upstream_link = self.colorify("yellow", self.proxy + torrent_link)
                        print("\n\nUpstream link: {url}\n".format(url=upstream_link))
                    elif temp2 == 'l':
                        try:
                            self.logger.debug("Loading torrent to client")
                            self.load_torrent(req_magnetic_link)
                        except Exception as e:
                            self.logger.exception(e)
                            continue
            except (ValueError, IndexError, TypeError) as e:
                print("\nBad Input!")
                self.logger.exception(e)
                continue

    def show_files(self, torrent_link):
        """To fetch and print files available in torrent."""
        self.logger.debug("Show torrent files selected")
        self.logger.debug("Torrent has %d files" %(int(self.file_count)))
        if int(self.file_count) > 0:
            soup = self.http_request(self.proxy + torrent_link)
            print("\nTotal %d files" % (int(self.file_count)))
            for i in range(int(self.file_count)):
                name = soup.find_all("tr")[i+1].find_all('td')[0].string
                size = soup.find_all("tr")[i+1].find_all('td')[1].string
                print("> %s  (%s)" % (name, self.colorify("green", size)))
        self.logger.debug("Files fetched!")


def main(title, page_limit):
    """Execution begins here."""
    try:
        print("\n[SkyTorrents]\n")
        print("Obtaining proxies...")
        sky = SkyTorrents(title, page_limit)
        sky.check_proxy()
        if title is None:
            sky.get_top_html()
        sky.get_html()
        sky.parse_html()
        sky.after_output_text()
        sky.select_torrent()
    except KeyboardInterrupt:
        sky.logger.debug("Keyboard interupt! Exiting!")
        print("\n\nAborted!")


if __name__ == "__main__":
    print("Its a module!")
