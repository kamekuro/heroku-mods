__version__ = (1, 0, 0)

#          █ █ █▀▀ ▀▄▄▀ ▄▀█ █▀▄▀█ █▀▄▀█ ▀█▀ █▄ █
#          █▀█ ██▄ ▄▀▀▄ █▀█ █ ▀ █ █ ▀ █ ▄█▄ █ ▀█ ▄
#            ✈ https://t.me/hexammin

# meta developer: @hexammods
# meta banner: https://github.com/kamekuro/heroku-mods/raw/master/banner.png
# meta pic: https://github.com/kamekuro/heroku-mods/raw/master/pics/debugmod.png

import inspect
import logging
import os

from telethon import types

from .. import loader, utils


logger = logging.getLogger(__name__)

DEBUG_MODS_DIR = os.path.join(utils.get_base_dir(), "debug_modules")
os.makedirs(DEBUG_MODS_DIR, mode=0o755, exist_ok=True)
for mod in os.scandir(DEBUG_MODS_DIR):
    os.remove(mod.path)


@loader.tds
class DebugMod(loader.Module):
    """Module for debug your modules"""

    strings = {
        "name": "DebugMod",
        "bad_module": "<emoji document_id=5355133243773435190>🚫</emoji> <b>Module not found. Use <code>.debugmod <module_name></code></b>",
        "debugging_enabled": "<emoji document_id=5332533929020761310>✅</emoji> <b>Debugging mode enabled for module</b> <code>{0}</code>\n<i>Go to directory named <code>heroku/debug_modules</code>, edit file named <code>{0}.py</code> and see changes in real time</i>",
        "debugging_disabled": "<emoji document_id=5332533929020761310>✅</emoji> <b>Debugging disabled</b>"
    }

    strings_ru = {
        "_cls_doc": "Модуль для дебаггинга ваших модулей",
        "bad_module": "<emoji document_id=5355133243773435190>🚫</emoji> <b>Модуль не найден. Используй <code>.debugmod <module_name></code></b>",
        "debugging_enabled": "<emoji document_id=5332533929020761310>✅</emoji> <b>Режим разработчика включен для модуля</b> <code>{0}</code>\n<i>Отправляйся в директорию <code>heroku/debug_modules<code>, изменяй файл <code>{0}.py</code>, и смотри изменения в режиме реального времени</i>",
        "debugging_disabled": "<emoji document_id=5332533929020761310>✅</emoji> <b>Режим разработчика выключен</b>"
    }

    def __init__(self):
        self._memory = {}
        self.watchdog.start()

    @loader.loop(interval=1, autostart=True)
    async def watchdog(self):
        if not os.path.isdir(DEBUG_MODS_DIR):
            return

        try:
            for module in os.scandir(DEBUG_MODS_DIR):
                last_modified = os.stat(module.path).st_mtime
                cls_ = module.path.split("/")[-1].split(".py")[0]

                if cls_ not in self._memory:
                    self._memory[cls_] = last_modified
                    continue

                if self._memory[cls_] == last_modified:
                    continue

                self._memory[cls_] = last_modified
                logger.debug("Reloading debug module %s", cls_)
                logger.critical(module.path)
                with open(module.path, "r") as f:
                    try:
                        await next(
                            module
                            for module in self.allmodules.modules
                            if module.__class__.__name__ == "LoaderMod"
                        ).load_module(
                            f.read(),
                            None,
                            save_fs=False,
                        )
                    except Exception:
                        logger.exception("Failed to reload module in watchdog")
        except Exception:
            logger.exception("Failed debugging watchdog")
            return


    @loader.command(
        ru_doc="включить/выключить режим отладки для ваших модулей"
    )
    async def debugmod(self, message: types.Message):
        """enable/disable debug mod for your modules"""

        args = utils.get_args_raw(message)
        instance = None
        for module in self.allmodules.modules:
            if (
                module.__class__.__name__.lower() == args.lower()
                or module.strings["name"].lower() == args.lower()
            ):
                if os.path.isfile(
                    os.path.join(
                        DEBUG_MODS_DIR,
                        f"{module.__class__.__name__}.py",
                    )
                ):
                    os.remove(
                        os.path.join(
                            DEBUG_MODS_DIR,
                            f"{module.__class__.__name__}.py",
                        )
                    )

                    try:
                        delattr(module, "heroku_debug")
                    except AttributeError:
                        pass

                    await utils.answer(message, self.strings("debugging_disabled"))
                    return

                module.heroku_debug = True
                instance = module
                break

        if not instance:
            await utils.answer(message, self.strings("bad_module"))
            return

        with open(
            os.path.join(
                DEBUG_MODS_DIR,
                f"{instance.__class__.__name__}.py",
            ),
            "wb",
        ) as f:
            f.write(inspect.getmodule(instance).__loader__.data)

        await utils.answer(
            message,
            self.strings("debugging_enabled").format(instance.__class__.__name__),
        )
