import math
import re
from urllib.parse import urljoin
from tqdm import tqdm
import pandas as pd

from baseCrawler import *
from collections import OrderedDict
global_ncols = 70


class NssCrawler(BaseCrawler):

    def __init__(self, court, html, options):
        super().__init__(court=court, html=html, options=options)
        self.create_directories(out_dir=options.dir,
                                log_dir="log_" + court, html=html)
        logger = logging.getLogger(self.__class__.__name__)
        logger.debug(options)

    def prepare_record(self, soup, id=None):
        pass

    def how_many(self, displayed_records):
        """
        Find number of records and compute count of pages.

        :type displayed_records: int
        :param displayed_records: number of displayed records
        """

        info_elem, resources = self.session.evaluate(
            "document.getElementById('_ctl0_ContentPlaceMasterPage__ctl0_pnPaging1_Repeater3__ctl0_Label2').innerHTML")

        if info_elem:
            # number_of_records = "20" #hack pro testovani
            str_info = info_elem.replace("<b>", "").replace("</b>", "")

        p_re_records = re.compile(r'(\d+)$')

        m = p_re_records.search(str_info)
        number_of_records = m.group(1)
        count_of_pages = math.ceil(
            int(number_of_records) / int(displayed_records))
        logger.info("records: %s => pages: %s",
                    number_of_records, count_of_pages)
        return number_of_records, count_of_pages

    def walk_pages(self, count_of_pages, case_type):
        """
        make a walk through pages of results

        :param count_of_pages: over how many pages we have to go
        :param case_type: name of type for easier identification of problem

        """
        session = self.session

        last_file = str(count_of_pages) + "_" + case_type + ".html"
        if os.path.exists(join(self.dir_path["html"], last_file)):
            logger.debug("Skip %s type <-- '%s' exists" %
                         (case_type, last_file))
            return True
        logger.debug("count_of_pages: %d", count_of_pages)
        positions = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        t = range(1, count_of_pages + 1)
        if self.options.progress:
            t = tqdm(t, ncols=global_ncols)  # progress progress bar
        for i in t:  # walk pages
            response = session.content
            #soup = BeautifulSoup(response,"html.parser")
            html_file = str(i) + "_" + case_type + ".html"
            if not os.path.exists(join(self.dir_path["html"], html_file)):
                if session.exists("#_ctl0_ContentPlaceMasterPage__ctl0_grwA"):
                    self.extract_data(response, html_file)
                    pass
            else:
                logger.debug("Skip file '%s'" % html_file)

            # TO DO - danger
            if i >= 12 and count_of_pages > 22:
                logger.debug("(%d) - %d < 10 --> %s <== (count_of_pages ) - (i) < 10 = Boolean", count_of_pages, i,
                             count_of_pages - i < 10)
                # special compute for last pages
                if count_of_pages - (i + 1) < 10:
                    logger.debug(
                        "positions[(i-(count_of_pages))] = %d", positions[(i - count_of_pages)])
                    page_number = str(positions[(i - count_of_pages)] + 12)
                else:
                    page_number = "12"  # next page element has constant ID
            else:
                page_number = str(i + 1)  # few first pages

            logger.debug("Number = %s", page_number)

            if self.options.screens:
                session.capture_to(join(self.dir_path["screens"], "find_screen_" + case_type + "_0" + str(i) + ".png"),
                                   None,
                                   selector="#pagingBox0")

            if session.exists(
                    "#_ctl0_ContentPlaceMasterPage__ctl0_pnPaging1_Repeater2__ctl" + page_number + "_LinkButton1") and i + 1 < (
                    count_of_pages + 1):
                #link_id = "_ctl0_ContentPlaceMasterPage__ctl0_pnPaging1_Repeater2__ctl"+page_number+"_LinkButton1"
                link = "_ctl0:ContentPlaceMasterPage:_ctl0:pnPaging1:Repeater2:_ctl" + \
                       page_number + ":LinkButton1"
                logger.debug("\tGo to next - Page %d (%s)", (i + 1), link)
                try:
                    # result, resources = session.click("#"+link_id,
                    # expect_loading=True)
                    session.evaluate(
                        "WebForm_DoPostBackWithOptions(new WebForm_PostBackOptions(\"%s\", \"\", true, \"\", \"\", false, true))" % link,
                        expect_loading=True)
                    #session.wait_for(page_has_loaded,"Timeout - next page",timeout=main_timeout)
                    logger.debug("New page was loaded!")
                except Exception:
                    logger.error(
                        "Error (walk_pages) - close browser", exc_info=True)
                    logger.debug("error_(" + str(i + 1) + ").png")
                    session.capture_to(
                        join(self.dir_path["screens"], "error_(" + str(i + 1) + ").png"))
                    return False
        return True

    def view_data(self, row_count):
        """
    sets forms parameters for viewing data

    :param row_count: haw many record would be showing on page
    """

        # time.sleep(1)

        session = self.session

        if session.exists("#_ctl0_ContentPlaceMasterPage__ctl0_rbRozhodnuti_1"):
            logger.debug("Select - radio")
            session.set_field_value(
                "#_ctl0_ContentPlaceMasterPage__ctl0_rbRozhodnuti_1", "0")
        if session.exists("#_ctl0_ContentPlaceMasterPage__ctl0_ddlSortName"):
            session.set_field_value(
                "#_ctl0_ContentPlaceMasterPage__ctl0_ddlSortName",
                "4"
            )
            session.set_field_value(
                "#_ctl0_ContentPlaceMasterPage__ctl0_ddlSortDirection",
                "0"
            )

        # click on find button
        if session.exists("#_ctl0_ContentPlaceMasterPage__ctl0_btnFind"):
            logger.debug("Click - find")
            session.click(
                "#_ctl0_ContentPlaceMasterPage__ctl0_btnFind", expect_loading=True)

        # change value of row count on page
        if session.exists("#_ctl0_ContentPlaceMasterPage__ctl0_ddlRowCount"):
            logger.debug("Change row count")
            session.set_field_value(
                "#_ctl0_ContentPlaceMasterPage__ctl0_ddlRowCount", str(row_count))

        if session.exists("#_ctl0_ContentPlaceMasterPage__ctl0_btnChangeCount"):
            logger.debug("Click - Change")
            result, resources = session.click("#_ctl0_ContentPlaceMasterPage__ctl0_btnChangeCount",
                                              expect_loading=True)

    def make_record(self, record):
        """
        extract relevant data from page

        :param soup: bs4 soup object

        """
        columns = record.findAll("td")  # columns of table in the row

        case_number = columns[1].getText().replace("\n", '').strip()
        # extract decision results

        link_elem = columns[1].select_one('img[src=/Image/evidencnilist.gif]')
        p_re_link = re.compile(r"window\.open\('/([^']+)'\)")
        m = p_re_link.search(link_elem["onclick"])
        if m:
            link = m.group(1)
            link = urljoin(self.url[self.court]["base"], link)
        if link_elem["style"] == "display:none;":
            link = None

        # registry mark isn't case number
        mark = case_number.split("-")[0].strip()

        item = {
            "registry_mark": mark,
            "order_number": case_number,
            "has_legal_sentences": True if link else False,
            "legal_sentences_url": link
        }
        logger.debug(item)
        return item

    def save_record(self, to_csv):
        frame = pd.DataFrame.from_records(to_csv)
        frame.to_csv(join(self.dir_path["working"], self.options.filename),
                     sep=";", index=False,
                     columns=["registry_mark", "order_number", "has_legal_sentences", "legal_sentences_url"])

    def extract_page(self, soup):
        table = soup.find(
            "table", id="_ctl0_ContentPlaceMasterPage__ctl0_grwA")
        rows = table.findAll("tr")
        logger.debug("Records on pages: %d" % len(rows[1:]))
        on_page = []
        for record in rows[1:]:
            on_page.append(self.make_record(record))
        return on_page

    def extract_information(self, saved_pages, extract=None):
        """
        extract informations from HTML files and write to CSVs

        :param saved_pages: number of all saved pages
        :type extract: bool
        :param extract: flag which indicates type of extraction

        """

        html_files = [join(self.dir_path["html"], fn)
                      for fn in next(os.walk(self.dir_path["html"]))[2]]
        to_csv = []
        if len(html_files) == saved_pages or extract:
            t = html_files

            if self.options.progress:
                t = tqdm(t, ncols=global_ncols)
            for html_f in t:
                logger.debug(html_f)
                soup = self.make_soup(html_f)
                to_csv.extend(self.extract_page(soup))

        else:
            logger.warning("Count of 'saved_pages'({}) and saved files({}) is differrent!".format(
                saved_pages, len(html_files)))
        self.save_record(to_csv)


def parameters():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    parser.add_option("-d", "--output-directory", action="store", type="string", dest="dir", default="output_dir",
                      help="Path to output directory")
    parser.add_option("-c", "--capture", action="store_true", dest="screens", default=False,
                      help="Capture screenshots?")
    parser.add_option("-o", "--output-file", action="store", type="string", dest="filename", default="metadata.csv",
                      help="Name of output CSV file")
    parser.add_option("-e", "--extraction", action="store_true", dest="extraction", default=False,
                      help="Make only extraction without download new data")
    parser.add_option("--progress-bar", action="store_true", dest="progress", default=False,
                      help="Show progress bar during operations")
    parser.add_option("--view", action="store_true", dest="view", default=False,
                      help="View window during operations")
    (options, args) = parser.parse_args()

    # print(args,options,type(options))
    return options


if __name__ == "__main__":
    crawler = NssCrawler(court="nss", html="html", options=parameters())
    logger = crawler.logger

    print(crawler.dir_path)

    if crawler.options.screens:
        crawler.session.capture_to(
            join(crawler.dir_path["screens"], "_find_screen.png"))

    if crawler.options.extraction:
        crawler.extract_information(None, extract=True)
    else:
        crawler.make_connection()
        row_count = 30
        crawler.view_data(row_count)
        records, pages = crawler.how_many(row_count)
        crawler.walk_pages(pages, "all")
