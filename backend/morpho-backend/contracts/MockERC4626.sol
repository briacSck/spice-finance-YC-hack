// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Minimal, self-contained ERC-4626 vault for testnet integration tests.
/// No caps, no gating — just standard deposit/withdraw/redeem so we can verify
/// the morpho-backend onchain path end-to-end. Asset is 6-dp USDC; shares 18-dp.
interface IERC20 {
    function transfer(address to, uint256 a) external returns (bool);
    function transferFrom(address f, address t, uint256 a) external returns (bool);
    function balanceOf(address) external view returns (uint256);
}

contract MockERC4626 {
    IERC20 public immutable assetToken;
    uint8 public constant decimals = 18;
    string public name = "Test Vault USDC";
    string public symbol = "tvUSDC";
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    constructor(address _asset) { assetToken = IERC20(_asset); }

    function asset() external view returns (address) { return address(assetToken); }
    function totalAssets() public view returns (uint256) { return assetToken.balanceOf(address(this)); }

    function convertToShares(uint256 assets) public view returns (uint256) {
        uint256 ts = totalSupply; uint256 ta = totalAssets();
        return (ts == 0 || ta == 0) ? assets * 1e12 : assets * ts / ta;
    }
    function convertToAssets(uint256 shares) public view returns (uint256) {
        uint256 ts = totalSupply;
        return ts == 0 ? shares / 1e12 : shares * totalAssets() / ts;
    }
    function maxDeposit(address) external pure returns (uint256) { return type(uint256).max; }
    function maxWithdraw(address owner) external view returns (uint256) { return convertToAssets(balanceOf[owner]); }
    function previewDeposit(uint256 a) external view returns (uint256) { return convertToShares(a); }
    function previewWithdraw(uint256 a) public view returns (uint256) {
        uint256 ts = totalSupply; uint256 ta = totalAssets();
        return (ts == 0 || ta == 0) ? a * 1e12 : (a * ts + ta - 1) / ta; // round up
    }

    function _mint(address to, uint256 s) internal { totalSupply += s; balanceOf[to] += s; }
    function _burn(address from, uint256 s) internal { balanceOf[from] -= s; totalSupply -= s; }

    function deposit(uint256 assets, address receiver) external returns (uint256 shares) {
        shares = convertToShares(assets);
        require(assetToken.transferFrom(msg.sender, address(this), assets), "transferFrom");
        _mint(receiver, shares);
    }
    function withdraw(uint256 assets, address receiver, address owner) external returns (uint256 shares) {
        shares = previewWithdraw(assets);
        if (msg.sender != owner) {
            uint256 a = allowance[owner][msg.sender];
            require(a >= shares, "allowance"); allowance[owner][msg.sender] = a - shares;
        }
        _burn(owner, shares);
        require(assetToken.transfer(receiver, assets), "transfer");
    }
    function redeem(uint256 shares, address receiver, address owner) external returns (uint256 assets) {
        assets = convertToAssets(shares);
        if (msg.sender != owner) {
            uint256 a = allowance[owner][msg.sender];
            require(a >= shares, "allowance"); allowance[owner][msg.sender] = a - shares;
        }
        _burn(owner, shares);
        require(assetToken.transfer(receiver, assets), "transfer");
    }
    function approve(address spender, uint256 amt) external returns (bool) {
        allowance[msg.sender][spender] = amt; return true;
    }
    function transfer(address to, uint256 amt) external returns (bool) {
        balanceOf[msg.sender] -= amt; balanceOf[to] += amt; return true;
    }
}
