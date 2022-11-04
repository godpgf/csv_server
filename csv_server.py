import logging
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.gen
from tornado.options import define, options
import tornado.log
import os
import argparse
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--log_path', type=str, default="./log/main.log", help="日志文件")
parser.add_argument('--csv_path', type=str, default="./csv", help="日志文件")
parser.add_argument('--port', type=int, default=80, help="服务端口")
parser.add_argument('--sep', type=str, default=',', help="分隔符")
args = parser.parse_args()

if not os.path.exists(os.path.dirname(args.log_path)):
    os.mkdir(os.path.dirname(args.log_path))

logging.basicConfig(level=logging.DEBUG,  # 控制台打印的日志级别
                    filename=args.log_path,
                    filemode='a',  # 模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                    # a是追加模式，默认如果不写的话，就是追加模式
                    format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                    # 日志格式
                    )

content = "<!doctype html><html><head><meta charset='utf-8'><title>[@title]</title></head><body>[@body]</body></html>"


def except2str(e):
    msg = '发生错误的文件：%s\t' % str(e.__traceback__.tb_frame.f_globals['__file__'])
    msg += '错误所在的行号：%s\t' % str(e.__traceback__.tb_lineno)
    msg += '错误信息：%s' % str(e.args)
    return msg


class Application(tornado.web.Application):
    def __init__(self, handlers, settings):
        super(Application, self).__init__(handlers, **settings)


class CSVMessage(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        try:
            file_list = []
            for file in os.listdir(args.csv_path):
                if file.endswith(".csv"):
                    file_list.append(file)
            if len(file_list) == 0:
                yield self.write("没有结果，打电话联系我！")
            else:
                file = file_list[-1]
                df = pd.read_csv(os.path.join(args.csv_path, file), sep=args.sep, encoding="utf8")
                columns = df.columns.values
                msg = "<table><tr>"
                for column in columns:
                    msg = msg + "<td>%s</td>" % column
                msg = msg + "</tr>"
                for i, line in df.iterrows():
                    msg = msg + "<tr>"
                    for column in columns:
                        msg = msg + "<td>%s</td>" % line[column]
                    msg = msg + "</tr>"
                msg = msg + "</table>"
            yield self.write(content.replace("[@title]", file).replace("[@body]", msg))
        except Exception as e:
            logging.error("ERROR~~~: %s %s" % (self.request.full_url(), except2str(e)))
            yield self.write("error")
        finally:
            yield self.finish()


def main():
    settings = {
        "title": "stock",
    }

    app = Application(
        handlers=[
            (r"/msg", CSVMessage),  # 存活探针
        ],
        settings=settings
    )

    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(args.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
