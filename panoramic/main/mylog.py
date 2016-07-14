import logging
logging.basicConfig(level=logging.WARNING,
                    format='\n%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S',
                    filename='/opt/oracle/apache/htdocs/panoramic/logs/error.log',
                    filemode='a')
mylog = logging.getLogger()
