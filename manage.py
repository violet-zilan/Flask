import os
from app import create_app,db
from flask_script import Manager, Shell
from flask_migrate import Migrate,MigrateCommand
from app.models import  User, Role, Post
COV = None
if os.environ.get('FLASK_COVERAGE'):
	import coverage
	COV = coverage.coverage(branch=True, include='app/*')
	COV.start()
#创建程序
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
#实例化
manager = Manager(app)
migrate = Migrate(app, db)
#返回对象
def make_shell_context():
	return dict(app=app, db=db, User=User, Role=Role, Post=Post)
#添加命令脚本
manager.add_command('shell',Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)
@manager.command
def deploy():
	"""Run deployment tasks."""
	from flask_migrate import upgrade
	from app.models import Role, User
	# 把数据库迁移到最新修订版本
	upgrade()
	# 创建用户角色
	Role.insert_roles()
	# 让所有用户都关注此用户
	User.add_self_follows()
@manager.command
def profile(length=25, profile_dir=None):
	"""Start the application under the code profiler."""
	from werkzeug.contrib.profiler import ProfilerMiddleware
	app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
	                                  profile_dir=profile_dir)
	app.run()
@manager.command
def test(coverage=False):
	"""Run the unittest"""
	if coverage and not os.environ.get('FLASK_COVERAGE'):
		import sys
		os.environ['FLASK_COVERAGE'] = '1'
		os.execvp(sys.executable, [sys.executable]+ sys.argv)
	import unittest
	tests = unittest.TestLoader().discover('tests')
	unittest.TextTestRunner(verbosity=2).run(tests)
	if COV:
		COV.stop()
		COV.save()
		print('Coverage Summary:')
		COV.report()
		basedir = os.path.abspath(os.path.dirname(__file__))
		covdir = os.path.join(basedir, 'tmp/coverage')
		COV.html_report(directory=covdir)
		print('HTML version: file://%s/index.html' % covdir)
		COV.erase()
if __name__ == '__main__':
	manager.run()