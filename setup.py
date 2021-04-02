from setuptools import setup

setup(
    name='prometheusrock',
    version='0.2.0',
    author='Nikita Kozhushko (kozhushman)',
    author_email='kozhushman@gmail.com',
    packages=['prometheusrock'],
    license='MIT License',
    url="https://github.com/kozhushman/prometheusrock",
    description='Prometheus middleware for Starlette and FastAPI',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "starlette",
        "prometheus_client"
    ],
)
