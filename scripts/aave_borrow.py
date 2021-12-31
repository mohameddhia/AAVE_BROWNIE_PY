from brownie import network, interface
from brownie.network.web3 import Web3
from scripts.helpful_script import get_account, FORKED_LOCAL_ENVIRONMENTS
from scripts.get_weth import get_weth
from brownie import network, config

amount = Web3.toWei(0.1, "ether")


def main():
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    get_weth()
    # get_weth contract
    # ABI
    # Addess
    lending_pool = get_lending_pool()
    # approve sending ERC20 token
    # approve_erc20()
    approve_erc20(amount, lending_pool.address, erc20_address, account)
    print("Depositing ...")
    tx = lending_pool.deposit(
        erc20_address, amount, account.address, 0, {"from": account}
    )  # referal code is deprecated put 0
    tx.wait(1)
    print("deposited")
    ## How much we need to borrow
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    # DAI in termis of ETH
    dai_eth_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    # Borrowable ETH -> borrowable DAI * 95%
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    print(f"We are going to borrow  {amount_dai_to_borrow} DAI")
    # now we will borrow
    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        Web3.toWei(amount_dai_to_borrow, "ether"),
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    print("We borrowed some DAI")
    get_borrowable_data(lending_pool, account)
    repay_all(amount, lending_pool, account)
    print("repay with ether , dai and chainlink")


def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )
    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account},
    )
    repay_tx.wait(1)
    print("Repay")


def get_asset_price(price_feed_address):
    # ABI
    # ADDRESS
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    print(f"the DAI/ETH is {Web3.fromWei(latest_price, 'ether')}")
    return float(latest_price)


def get_borrowable_data(lending_pool, account):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    print(f"you have {total_collateral_eth} worth of ETH deposited.")
    print(f"you have {total_debt_eth} worth of ETH borrowed.")
    print(f"you can borrow {available_borrow_eth} worthof ETH .")
    return (float(available_borrow_eth), float(total_debt_eth))


def approve_erc20(amount, spender, erc20_address, account):
    print("approving")
    erc20 = interface.IERC20(
        erc20_address,
    )
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("approved")
    return tx
    # We need
    # ABI
    # ADDRESS


def get_lending_pool():
    # ABI
    # Address
    lending_pool_address_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_address_provider"]
    )
    lending_pool_address = lending_pool_address_provider.getLendingPool()
    # ABI
    # Address
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool
