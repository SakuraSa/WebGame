#!/usr/bin/env python
# coding = utf-8

"""
Page
"""

__author__ = 'Rnd495'

import traceback

import tornado.web
import tornado.gen

import core.models
from core import verification
from core.models import User, Monster
from core.configs import Configs
from UI.Manager import mapping

configs = Configs.instance()


class Interruption(Exception):
    """
    Interruption
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

    def render(self, page):
        raise NotImplementedError()


class NoticeAndRedirectInterruption(Interruption):
    """
    NoticeAndRedirectInterruption
    """
    JUMP_BACK = '::JUMP_BACK::'

    def __init__(self, message, title='Notice', redirect_to=None, countdown=3, style='info'):
        self.message = message
        self.title = title
        self.countdown = countdown
        self.redirect_to = redirect_to if redirect_to is not None else self.JUMP_BACK
        self.style = style

    def render(self, page):
        page.render('noticeAndRedirect.html',
                    message=self.message,
                    title=self.title,
                    countdown=self.countdown,
                    redirect_to=self.redirect_to,
                    style=self.style)


class PageBase(tornado.web.RequestHandler):
    """
    PageBase
    """
    def __init__(self, application, request, **kwargs):
        tornado.web.RequestHandler.__init__(self, application, request, **kwargs)
        self._db = None

    @property
    def db(self):
        if self._db is None:
            self._db = core.models.get_new_session()
        return self._db

    def get_current_user(self):
        user_id = self.get_secure_cookie("user_id", None)
        if user_id:
            db = core.models.get_new_session()
            current_user = db.query(User).filter(User.user_id == user_id).first()
            db.close()
        else:
            current_user = None
        return current_user

    def get_login_url(self):
        return '/login'

    def data_received(self, chunk):
        return tornado.web.RequestHandler.data_received(self, chunk)

    def write_error(self, status_code, **kwargs):
        error_type, error_instance, trace = kwargs.pop('exc_info')
        if issubclass(error_type, Interruption):
            error_instance.render(self)
            return
        if configs.show_error_details:
            message = traceback.format_exc()
        else:
            message = None
        self.render('error.html', status_code=status_code, message=message)

    def _handle_request_exception(self, e):
        if not isinstance(e, Interruption):
            return tornado.web.RequestHandler._handle_request_exception(self, e)

        import sys
        from tornado import httputil
        from tornado.log import gen_log

        if isinstance(e, tornado.web.Finish):
            # Not an error; just finish the request without logging.
            if not self._finished:
                self.finish()
            return
        if self._finished:
            # Extra errors after the request has been finished should
            # be logged, but there is no reason to continue to try and
            # send a response.
            return
        if isinstance(e, tornado.web.HTTPError):
            if e.status_code not in tornado.httputil.responses and not e.reason:
                gen_log.error("Bad HTTP status code: %d", e.status_code)
                self.send_error(500, exc_info=sys.exc_info())
            else:
                self.send_error(e.status_code, exc_info=sys.exc_info())
        else:
            self.send_error(500, exc_info=sys.exc_info())

    def get_referer(self):
        return self.request.headers.get('referer', None)

    def get_converted_param(self, param_name, convert_function):
        param_str = self.get_argument(param_name, None)
        if param_str is None:
            return dict(
                success=False,
                reason='param "%s" not found.' % param_name,
                error_msg='',
                data=None)
        try:
            data = convert_function(param_str)
        except Exception as error:
            return dict(
                success=False,
                reason='illegal param "%s" = "%s".' % (param_name, param_str),
                error_msg=error.message,
                data=None)
        return dict(
            success=True,
            reason='ok',
            error_msg='',
            data=data)

    def get_user(self):
        if not self.current_user:
            return dict(
                success=False,
                reason='need login first'
            )
        user_id = self.get_argument('user_id', None)
        if user_id is None:
            user = self.current_user
        else:
            user = self.db.query(User).filter(User.user_id == user_id).first()
            self.db.close()
            if not user:
                return dict(
                    success=False,
                    reason='user is not found by user_id = "%s"' % user_id
                )
        return dict(
            success=True,
            reason='ok',
            user=user
        )


@mapping('/login')
class PageLogin(PageBase):
    """
    PageLogin
    """
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

    def get(self):
        next_page = self.get_argument('next', '/')
        if self.current_user:
            self.redirect(next_page)
        return self.render('login.html', next=next_page)

    @verification.check
    def post(self):
        username = self.get_body_argument('username')
        password = self.get_body_argument('password')
        remember = self.get_body_argument('remember-me', True)
        self.login(self, username, password, remember)
        if self.current_user:
            redirect = self.get_argument('next', '/')
            self.redirect(redirect)
        else:
            raise NoticeAndRedirectInterruption(
                message='username or password incorrect.',
                title='Login error',
                redirect_to=None,
                countdown=10, style='warning')

    @staticmethod
    def login(page, username, password, remember=True):
        password = User.password_hash(password)
        expire = 30 if remember else 1
        user = page.db.query(User).filter(User.user_name == username, User.user_pass == password).first()
        page.db.close()
        if user:
            page.set_secure_cookie("user_id", str(user.user_id), expire)
            page.current_user = user
            return user
        else:
            page.clear_cookie("user_id")
            return None


@mapping('/logout')
class PageLogout(PageBase):
    """
    PageLogout
    """
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

    def get(self):
        self.logout(self)
        redirect = self.get_argument('next', '/')
        self.redirect(redirect)

    @staticmethod
    def logout(page):
        page.clear_cookie('user_id')
        page.current_user = None


@mapping('/register')
class PageRegister(PageBase):
    """
    PageRegister
    """
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

    def get(self):
        self.render('register.html')

    @verification.check
    def post(self):
        username = self.get_body_argument('username')
        password = self.get_body_argument('password')
        password_confirm = self.get_body_argument('password_confirm')

        # register param check
        # password confirm
        if password != password_confirm:
            raise NoticeAndRedirectInterruption(
                message='password dismatch with password confirm.',
                title='register error', redirect_to='/register',
                countdown=10)
        # username availability check
        result = APIGetUsernameAvailability.check(username=username, check_exists=True)
        if not result['availability']:
            raise NoticeAndRedirectInterruption(
                message=result['reason'],
                title='register error', redirect_to='/register',
                countdown=10)
        # username availability check
        if not password:
            raise NoticeAndRedirectInterruption(
                message='password can not be empty',
                title='register error', redirect_to='/register',
                countdown=10)

        # register new user
        user = core.models.User(name=username, pwd=password, role_id=3)
        try:
            self.db.add(user)
            self.db.commit()
        except:
            self.db.rollback()
            raise
        finally:
            self.db.close()

        # redirect to login page
        self.redirect('/login')


@mapping('/')
class PageHome(PageBase):
    """
    PageHome
    """
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

    def get(self):
        return self.render('home.html')


@mapping('/api/get_username_availability')
class APIGetUsernameAvailability(PageBase):
    """
    APIGetUsernameAvailability

    api for register page
    check the availability of the username

    method: get
    param username: str
    result:
    {
      availability: bool,
      reason: str
    }
    """
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

    def get(self):
        username = self.get_query_argument('username')
        self.write(APIGetUsernameAvailability.check(username=username, check_exists=True))

    @classmethod
    def check(cls, username, check_exists=True):
        result = dict(availability=True, reason='ok')
        if not username:
            result = dict(availability=False, reason='username can not be empty.')
        elif len(username) > 16:
            result = dict(availability=False, reason='username "%s" is too long.' % username)
        elif check_exists:
            db = core.models.get_new_session()
            count = db.query(User).filter(User.user_name == username).count()
            db.close()
            if count > 0:
                result = dict(availability=False, reason='username "%s" is already exists.' % username)
        return result


@mapping('/api/create_verification_code')
class APICreateVerificationCode(PageBase):
    """
    APICreateVerificationCode

    api for verification code
    generate a new verification code

    method: get
    no param
    result:
    {
      uuid: str,
      image: str
    }
    """
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

    def get(self):
        code = verification.Verification.instance().new()
        self.write({'uuid': code.uuid, 'image': code.image})


@mapping('/api/check_verification_code')
class APICheckVerificationCode(PageBase):
    """
    APICheckVerificationCode

    api for verification code
    check the verification code

    method: get
    param ver_uuid: str
    param ver_code: str
    result:
    {
      success: bool,
      ok: bool
    }
    """
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

    def get(self):
        try:
            code = self.get_argument("ver_code")
            uuid = self.get_argument("ver_uuid")
        except tornado.web.HTTPError:
            self.write({'success': False, 'ok': False})
            return
        ok = verification.Verification.instance().check(uuid, code)
        self.write({'success': True, 'ok': ok})


@mapping('/api/user/login')
class APIUserLogin(PageBase):
    """
    APIUserLogin

    api for user login
    check username and password
    base64 = true while password is base64 encoded
    set session cookies

    method: get
    param username: str
    param password: str
    param remember-me: bool
    param base64: bool
    result:
    {
      success: bool,
      reason: str
    }
    """
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

    def get(self):
        self.write(self.login())

    def login(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        remember = self.get_argument('remember-me', None)
        base64 = self.get_argument('base64', None)
        if remember == 'false' or remember == 'False':
            remember = False
        if base64 and base64.lower() != 'false':
            try:
                password = password.decode('base64')
            except:
                return dict(
                    success=False,
                    reason='"%s" is not base64 encoded.' % password
                )
        success = PageLogin.login(self, username, password, remember)
        return dict(
            success=bool(success),
            reason='ok'
        )


@mapping('/api/user/logout')
class APIUserLogout(PageBase):
    """
    APIUserLogout

    api for user logout
    unset session cookies

    method: get
    no param
    result:
    {
      success: bool,
      reason: str
    }
    """
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

    def get(self):
        self.write(self.logout())

    def logout(self):
        PageLogout.logout(self)
        return dict(
            success=True,
            reason='ok'
        )


@mapping('/api/user/basic_info')
class APIUserBasicInfo(PageBase):
    """
    APIUserBasicInfo

    api to get basic info of the user
    this api needs login first
    when param user_id leaves blank
    this api returns basic info of current user

    method: get
    param user_id: int | null
    result:
    {
      success: bool,
      reason: str,
      data: {
        user_id: int,
        user_name: str,
        user_header_url: str | null,
        user_register_time: str     (%Y/%m/%d %H:%M:%S)
      } | null
    }
    """
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

    def get(self):
        self.write(self.get_basic_info())

    def get_basic_info(self):
        user_result = self.get_user()
        if not user_result['success']:
            return user_result
        else:
            user = user_result['user']

        # get user model dict
        data = user.to_dict()

        # drop secret field
        data.pop('user_pass')

        return dict(
            success=True,
            reason='ok',
            data=data
        )


@mapping('/api/user/has_monster/basic_info/list')
class APIUserHasMonsterBasicInfoList(PageBase):
    """
    APIUserHasMonsterBasicInfoList

    api to get basic info of the monster that user has
    this api needs login first
    when param user_id leaves blank
    this api returns basic info of current user

    method: get
    param user_id: int | null
    result:
    {
      success: bool,
      reason: str,
      data: [
      {
        monster_id: int,
        monster_name: str,
        monster_hp: int,
        monster_atk: int,
        monster_def: int,
        monster_spd: int,
        monster_sp_atk: int,
        monster_sp_def: int,
        monster_element_id: int,
        monster_rebirth: int,
        monster_exp: int,
        monster_level: int,
        monster_love: int,
        monster_hunger: int,
        monster_energy: int,
        monster_type_id: int,
        monster_owner_id: int
      },
      ...
      ]
    }
    """
    def __init__(self, application, request, **kwargs):
        PageBase.__init__(self, application, request, **kwargs)

    def get(self):
        self.write(self.get_monster_basic_info_list())

    def get_monster_basic_info_list(self):
        user_result = self.get_user()
        if not user_result['success']:
            return user_result
        else:
            user = user_result['user']

        session = core.models.get_new_session()
        monster_list = session.query(Monster).filter(Monster.monster_owner_id == user.user_id).all()
        monster_basic_info_list = [monster.to_dict() for monster in monster_list]
        return dict(
            success=True,
            reason='ok',
            data=monster_basic_info_list
        )